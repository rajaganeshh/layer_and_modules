resource "aws_iam_role" "iam_role" {
  name                    = var.role_name
  description             = var.role_name         
  assume_role_policy      = var.assume_role_policy
  force_detach_policies   = "true"
  max_session_duration    = var.max_session_duration
  tags                    = var.common_tags
}


resource "aws_iam_instance_profile" "serive_iam_role_instance_profile" {
  count                   = var.instance_profile_enabled == true ? 1 : 0
  name                    = "${var.role_name}_instance_profile"
  role                    = aws_iam_role.iam_role.name
}


resource "aws_iam_policy" "iam_policy" {
  for_each                = var.iam_policy
  name                    = "${each.value.name}"
  description             = "${each.value.description}"
  policy                  = each.value.policy
}


resource "aws_iam_role_policy_attachment" "policy_attach" {
  for_each   = aws_iam_policy.iam_policy
  role       = aws_iam_role.iam_role.name
  policy_arn = each.value["arn"]
}

resource "aws_iam_role_policy_attachment" "policy_attach_direct" {
  count      = length(var.policy_attach_role) > 0 ? length(var.policy_attach_role) : 0
  role       = aws_iam_role.iam_role.name
  policy_arn = var.policy_attach_role[count.index]
}
