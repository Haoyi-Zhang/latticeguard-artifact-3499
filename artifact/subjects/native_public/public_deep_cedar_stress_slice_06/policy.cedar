permit(principal in Role::"viewer", action == Action::"Read", resource == Repo::"RepoPublic");
forbid(principal in Role::"suspended", action == Action::"Read", resource == Repo::"RepoPublic");
