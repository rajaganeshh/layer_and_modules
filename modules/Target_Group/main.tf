
resource "aws_lb_target_group" "lb_target_group" {

  name                 = var.tg_name
  port                 = var.tg_port
  protocol             = var.tg_protocol
  vpc_id               = var.vpc_id
  target_type          = var.target_type
  deregistration_delay = var.deregistration_delay
  preserve_client_ip   = var.tg_preserve_client_ip
  slow_start           = var.tg_slow_start

  stickiness {
    type            = var.tg_sticky_type
    enabled         = var.tg_sticky_enabled
    cookie_duration = var.tg_sticky_duration
  }

  health_check {
    protocol            = var.hc_protocol == null ? var.tg_protocol : var.hc_protocol
    healthy_threshold   = var.tg_healthy_threshold
    unhealthy_threshold = var.tg_unhealthy_threshold
    path                = var.tg_path
    interval            = var.tg_health_interval
    timeout             = var.tg_health_timeout
    matcher             = var.hc_protocol == "TCP" ? null : var.tg_matcher
  }

  #  dynamic "target_health_state" {
  #    count = var.tg_port == "TCP" ? 1 : 0
  #    content {
  #      enable_unhealthy_connection_termination = false
  #    }
  #  }

  tags = var.common_tags
}
