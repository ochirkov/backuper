---

type: rds
action: restore
parameters:
  db_identifier: "rds-api-auth-{{ active_env }}"
  snapshot_identifier: "rds-api-auth-{{ backup_date }}"
  region: eu-west-2
