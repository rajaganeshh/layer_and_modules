resource "aws_lb" "alb" {
  name               = var.lb_name
  internal           = var.lb_internal
  load_balancer_type = var.lb_type
  security_groups    = var.lb_security_groups
  subnets            = var.lb_subnet_ids
  idle_timeout       = var.idle_timeout

  enable_deletion_protection = var.enable_deletion_protection

  tags = merge(var.common_tags,
  { Service = "Application Load Balancer" })
}

resource "aws_lb_listener" "port80" {
  count = var.add_port_80_listener ? 1 : 0

  load_balancer_arn = aws_lb.alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "There are no listeners for your request"
      status_code  = "404"
    }
  }

  tags = merge(var.common_tags,
  { Service = "alb-80-listener" })

}

resource "aws_lb_listener" "port4431" {
  count = var.add_port_4431_listener ? 1 : 0

  load_balancer_arn = aws_lb.alb.arn
  port              = "4431"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "There are no listeners for your request"
      status_code  = "404"
    }
  }

  tags = merge(var.common_tags,
  { Service = "alb-4431-listener" })
}

resource "aws_lb_listener" "port443" {
  count = var.add_port_443_listener ? 1 : 0

  load_balancer_arn = aws_lb.alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "There are no listeners for your request"
      status_code  = "404"
    }
  }

  tags = merge(var.common_tags,
  { Service = "alb-443-listener" })
}


resource "null_resource" "octo_env" {
  provisioner "local-exec" {
    command     = "start-sleep 5"
    interpreter = ["pwsh", "-Command"]
  }
}

resource "aws_lb_listener_certificate" "https_additional_certs" {
  count = length(var.additional_certificate_arn)

  listener_arn    = aws_lb_listener.port443[0].arn
  certificate_arn = var.additional_certificate_arn[count.index]
  depends_on      = [aws_lb_listener.port443]
}
