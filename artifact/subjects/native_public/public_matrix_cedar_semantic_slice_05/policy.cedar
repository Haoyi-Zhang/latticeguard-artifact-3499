permit(principal in Role::"viewer", action == Action::"Read", resource == Repo::"RepoReports");
forbid(principal in Role::"suspended", action == Action::"Read", resource == Repo::"RepoReports");
