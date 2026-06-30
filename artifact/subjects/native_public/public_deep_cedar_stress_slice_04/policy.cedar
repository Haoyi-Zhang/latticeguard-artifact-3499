permit(principal in Role::"viewer", action == Action::"Audit", resource == Repo::"RepoReports");
forbid(principal in Role::"suspended", action == Action::"Audit", resource == Repo::"RepoReports");
