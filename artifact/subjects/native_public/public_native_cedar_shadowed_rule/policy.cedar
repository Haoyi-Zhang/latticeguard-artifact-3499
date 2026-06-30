permit(principal in Role::"viewer", action == Action::"Read", resource == Repo::"Reports");
forbid(principal in Role::"suspended", action == Action::"Read", resource == Repo::"Reports");
