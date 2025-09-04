#!/usr/bin/env python3
"""
CSV → Ansible dynamic inventory (SOLID principles)
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict, OrderedDict
from typing import Dict, List, Any, Optional, Protocol


# Interfaces (Protocol classes for dependency inversion)
class ConfigProvider(Protocol):
   def get_csv_path(self) -> Path: ...
   def get_flags(self) -> Dict[str, bool]: ...
   def get_state_map(self) -> Dict[str, str]: ...


class DataReader(Protocol):
   def read(self, path: Path) -> List[Dict[str, Any]]: ...


class GroupStrategy(Protocol):
   def generate_groups(self, rows: List[Dict]) -> Dict[str, List[str]]: ...


class InventoryBuilder(Protocol):
   def build(self, rows: List[Dict]) -> Dict[str, Any]: ...


# Concrete implementations
class EnvConfig:
   """Single Responsibility: Environment configuration"""
   
   def __init__(self, cli_path: Optional[str] = None):
       self.cli_path = cli_path
       self.state_map = self._load_state_map()
   
   def get_csv_path(self) -> Path:
       if env_path := os.getenv("INV_CSV"):
           return Path(env_path).expanduser().resolve()
       if self.cli_path:
           return Path(self.cli_path).expanduser().resolve()
       return (Path(__file__).resolve().parent / "vm_data.csv").resolve()
   
   def get_flags(self) -> Dict[str, bool]:
       return {
           "group_by_owner": self._envflag("INV_GROUP_BY_OWNER", True),
           "group_by_state": self._envflag("INV_GROUP_BY_STATE", True),
           "group_by_custom": self._envflag("INV_GROUP_BY_CUSTOM", True),
       }
   
   def get_state_map(self) -> Dict[str, str]:
       return self.state_map
   
   def _envflag(self, name: str, default: bool) -> bool:
       v = os.getenv(name)
       if v is None:
           return default
       return v.lower() in ("1", "true", "yes", "on")
   
   def _load_state_map(self) -> Dict[str, str]:
       """Load state mappings from env or defaults"""
       custom_map = os.getenv("INV_STATE_MAP")
       if custom_map:
           try:
               return json.loads(custom_map)
           except json.JSONDecodeError:
               pass
       return {
           "on": "poweredon",
           "powered-on": "poweredon",
           "poweredon": "poweredon",
           "off": "poweredoff",
           "powered-off": "poweredoff",
           "poweredoff": "poweredoff",
           "del": "absent",
           "delete": "absent",
           "absent": "absent",
       }


class CSVReader:
   """Single Responsibility: CSV data reading"""
   
   def __init__(self, required_cols: Optional[set] = None):
       self.required_cols = required_cols or {"vm_name", "vm_ip_addr"}
   
   def read(self, path: Path) -> List[Dict[str, Any]]:
       if not path.exists():
           raise FileNotFoundError(f"CSV not found: {path}")
       
       rows = []
       with path.open("r", encoding="utf-8-sig", newline="") as f:
           reader = csv.DictReader(f)
           headers = [h.strip() for h in (reader.fieldnames or [])]
           
           if not headers:
               raise ValueError("Empty CSV or missing header")
           
           missing = self.required_cols - set(headers)
           if missing:
               raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
           
           for raw in reader:
               row = {k.strip(): (v.strip() if isinstance(v, str) else v) 
                      for k, v in raw.items()}
               if row.get("vm_name"):
                   rows.append(row)
       
       self._validate_uniqueness(rows)
       return rows
   
   def _validate_uniqueness(self, rows: List[Dict]) -> None:
       seen = {}
       dups = []
       for r in rows:
           name = r["vm_name"]
           if name in seen:
               dups.append(name)
           seen[name] = True
       if dups:
           sys.stderr.write(f"WARN: Duplicate vm_name: {', '.join(sorted(set(dups)))}\n")


class DynamicGrouper:
   """Single Responsibility: Group generation strategies"""
   
   def __init__(self, config: ConfigProvider):
       self.config = config
       self.flags = config.get_flags()
       self.state_map = config.get_state_map()
   
   def generate_groups(self, rows: List[Dict]) -> Dict[str, List[str]]:
       groups = defaultdict(list)
       
       for row in rows:
           hostname = row["vm_name"]
           
           # Custom group from vm_group column
           if self.flags.get("group_by_custom") and row.get("vm_groups"):
               for group in row["vm_groups"].split(","):
                   group = group.strip()
                   if group:
                       groups[f"{group}"].append(hostname)
           
           # Owner groups
           if self.flags.get("group_by_owner") and row.get("vm_owner"):
               groups[f"owner_{row['vm_owner']}"].append(hostname)
           
           # State groups
           if self.flags.get("group_by_state") and row.get("vm_state"):
               state = self._normalize_state(row["vm_state"])
               groups[f"state_{state}"].append(hostname)
           
           # Default group if no custom group
           if not any(hostname in hosts for group, hosts in groups.items() 
                     if group.startswith("vm_")):
               groups["ungrouped"].append(hostname)
       
       return dict(groups)
   
   def _normalize_state(self, state: str) -> str:
       return self.state_map.get((state or "").strip().lower(), "poweredon")


class AnsibleInventoryBuilder:
   """Single Responsibility: Build Ansible inventory format"""
   
   def __init__(self, grouper: GroupStrategy, config: ConfigProvider):
       self.grouper = grouper
       self.state_map = config.get_state_map()
   
   def build(self, rows: List[Dict]) -> Dict[str, Any]:
       hostvars = {}
       uuid_index = {}
       
       for row in rows:
           hostname = row["vm_name"]
           vm_uuid = row.get("vm_uuid", "")
           vm_uuid = None if (vm_uuid or "").lower() == "none" else vm_uuid
           
           # Pass all CSV columns as hostvars
           hostvar = {k: v for k, v in row.items()}
           
           # Add computed fields
           hostvar["ansible_host"] = row.get("vm_ip_addr", "")
           if "vm_state" in row:
               hostvar["vmware_state"] = self._normalize_state(row["vm_state"])
           
           hostvars[hostname] = hostvar
           
           if vm_uuid:
               uuid_index[vm_uuid] = hostname
       
       # Get groups
       groups = self.grouper.generate_groups(rows)
       
       # Build inventory
       inv = OrderedDict()
       inv["_meta"] = {"hostvars": hostvars}
       
       for group in sorted(groups):
           inv[group] = {"hosts": sorted(groups[group])}
       
       inv["all"] = {
           "children": sorted(groups.keys()),
           "vars": {"uuid_index": uuid_index}
       }
       
       return inv
   
   def _normalize_state(self, state: str) -> str:
       return self.state_map.get((state or "").strip().lower(), "poweredon")


class InventoryOutput:
   """Single Responsibility: Output formatting"""
   
   @staticmethod
   def as_json(data: Any) -> str:
       return json.dumps(data, indent=2, ensure_ascii=False)
   
   @staticmethod
   def print_list(inventory: Dict) -> None:
       print(InventoryOutput.as_json(inventory))
   
   @staticmethod
   def print_host(inventory: Dict, hostname: str) -> None:
       hostvars = inventory.get("_meta", {}).get("hostvars", {})
       print(InventoryOutput.as_json(hostvars.get(hostname, {})))


class Application:
   """Orchestrator: Coordinates all components"""
   
   def __init__(self):
       self.parser = self._create_parser()
   
   def _create_parser(self) -> argparse.ArgumentParser:
       p = argparse.ArgumentParser(description="CSV → Ansible dynamic inventory")
       p.add_argument("--list", action="store_true", help="Output full inventory")
       p.add_argument("--host", help="Output hostvars for a single host")
       p.add_argument("csv", nargs="?", help="CSV path")
       return p
   
   def run(self) -> None:
       args = self.parser.parse_args()
       
       try:
           # Setup components (Dependency Injection)
           config = EnvConfig(args.csv)
           reader = CSVReader(required_cols={
               "vm_name", "vm_state", "vm_ip_addr"
           })
           grouper = DynamicGrouper(config)
           builder = AnsibleInventoryBuilder(grouper, config)
           
           # Execute pipeline
           csv_path = config.get_csv_path()
           rows = reader.read(csv_path)
           inventory = builder.build(rows)
           
           # Output
           if args.host:
               InventoryOutput.print_host(inventory, args.host)
           else:
               InventoryOutput.print_list(inventory)
               
       except (FileNotFoundError, ValueError) as e:
           sys.stderr.write(f"ERROR: {e}\n")
           sys.exit(2)
       except Exception as e:
           sys.stderr.write(f"FATAL: {e}\n")
           sys.exit(1)


if __name__ == "__main__":
   app = Application()
   app.run()