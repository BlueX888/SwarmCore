package swarmcore

import rego.v1

default decision := {
  "allow": false,
  "obligations": {},
  "policyRevision": "local-bundle:v1",
  "reason": "role or scope does not grant the action",
}

admin_roles := {"tenant_admin"}
workload_actions := {
  "tool.execute",
  "tool.compensate",
  "model.invoke",
  "secret.read",
  "artifact.read",
  "artifact.write",
  "sandbox.execute",
  "webhook.deliver",
}

allowed if {
  some role in input.subject.roles
  role in admin_roles
}

allowed if {
  "workload" in input.subject.roles
  input.action in workload_actions
}

allowed if {
  input.action in input.subject.scopes
}

tool_obligations := {"requireApproval": true} if {
  input.action == "tool.execute"
  input.resource.risk in {"HIGH", "CRITICAL"}
}

tool_obligations := {} if {
  not input.action == "tool.execute"
}

tool_obligations := {} if {
  input.action == "tool.execute"
  not input.resource.risk in {"HIGH", "CRITICAL"}
}

decision := {
  "allow": true,
  "obligations": tool_obligations,
  "policyRevision": "local-bundle:v1",
} if {
  allowed
}
