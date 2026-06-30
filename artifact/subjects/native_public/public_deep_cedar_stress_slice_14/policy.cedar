permit(principal in Role::"viewer", action == Action::"Delete", resource == Repo::"AuditLog");
forbid(principal in Role::"suspended", action == Action::"Delete", resource == Repo::"AuditLog");
