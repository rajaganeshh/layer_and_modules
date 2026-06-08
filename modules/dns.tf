data "aws_route53_zone" "selected" {
#  count    = var.create_dns ? 1 : 0
  provider = aws.dnszone
  name     = var.route53_zone_name
  private_zone = true
}

resource "aws_route53_record" "alb_wildcard" {
  for_each = var.lb_dns_entry
  provider = aws.dnszone
  zone_id  = data.aws_route53_zone.selected.zone_id
  name     = "${each.value}${var.lb_dns_name}"
  type     = "A"

  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      zone_id
    ]
  }

  alias {
    name                   = aws_lb.alb.dns_name
    zone_id                = aws_lb.alb.zone_id
    evaluate_target_health = false
  }

  depends_on = [data.aws_route53_zone.selected]
}

#resource "aws_route53_record" "alb_root" {
#  count    = var.create_dns ? 1 : 0
#  provider = aws.dnszone
#  zone_id  = data.aws_route53_zone.selected[0].zone_id
#  name     = "${var.DNS_path}.${var.route53_zone_name}"
#  type     = "A"
#
#  alias {
#    name                   = aws_lb.alb.dns_name
#    zone_id                = aws_lb.alb.zone_id
#    evaluate_target_health = false
#  }
#}
