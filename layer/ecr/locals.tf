locals {


  ecr_repos = {
	frontend = { name = "frontend", mutability = "MUTABLE", scan_on_push = "true", ecr_repo_policy = data.template_file.custom_policy_frontend_repo.rendered , ecr_repo_lifecycle_policy = data.template_file.custom_policy_frontend_lifecycle.rendered }

	backend = { name = "backend", mutability = "MUTABLE", scan_on_push = "true", ecr_repo_policy = data.template_file.custom_policy_backend_repo.rendered , ecr_repo_lifecycle_policy = data.template_file.custom_policy_backend_lifecycle.rendered }

	middleware = { name = "middleware", mutability = "MUTABLE", scan_on_push = "true", ecr_repo_policy = data.template_file.custom_policy_middleware_repo.rendered , ecr_repo_lifecycle_policy = data.template_file.custom_policy_middleware_lifecycle.rendered }

	interface = { name = "interface", mutability = "MUTABLE", scan_on_push = "true", ecr_repo_policy = data.template_file.custom_policy_interface_repo.rendered , ecr_repo_lifecycle_policy = data.template_file.custom_policy_interface_lifecycle.rendered }

	}
}