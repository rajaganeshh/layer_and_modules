resource "aws_lb_listener_rule" "redirect_http_to_https" {
  count  = var.host_redirect == true ? 1 : 0
  listener_arn = var.lb_listener_arn


#dynamic "redirect" {
#      for_each = try([var.default_action.redirect], [])
#
#      content {
#        status_code = try(redirect.value.status_code, "HTTP_302")
#        host        = try(redirect.value.host, "#{host}")
#        path        = try(redirect.value.path, "/#{path}")
#        port        = try(redirect.value.port, "#{port}")
#        protocol    = try(redirect.value.protocol, "#{protocol}")
#        query       = try(redirect.value.query, "#{query}")
#      }
#    }
#  }

  action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
	  host        = "${var.service_host_redirect}.company-markettest.com"
	  path        = "/*"
    }
  }

  condition {
    host_header {
      values = [var.service_host_redirect]
    }
  }
  tags = var.common_tags
  
}


resource "aws_lb_listener_rule" "host_forward" {
  count    = var.host_forward == true  ? 1 : 0  
  listener_arn = var.lb_listener_arn
  priority     = var.priority

  action {
    type             = "forward"
	forward {
      target_group {
        arn    = var.target_group_arn
        weight = var.target_group_arn_weight
      }

      target_group {
        arn    = var.target_group_arn_green
        weight = var.target_group_arn_green_weight
      }
	  stickiness {
		enabled  = var.lb_sticky_enabled
		duration = var.lb_sticky_duration
	  }	  
	}
	
#    target_group_arn = var.target_group_arn
  }


  dynamic "condition" {
    for_each = length(var.service_path_pattern) > 0 ? [true] : []
    content {
      path_pattern {
        values = var.service_path_pattern
      }
    }
  }
  
#  condition {
#    path_pattern {
#      values = var.service_path_pattern
#    }
#  }

  condition {
    host_header {
      values = var.service_host_header
    }
  }
  
  tags = var.common_tags
}


resource "aws_lb_listener_rule" "path_pattern" {
  count    = var.host_path == true ? 1 : 0  
  listener_arn = var.lb_listener_arn
  priority     = var.priority

  action {
    type             = "forward"

	forward {
      target_group {
        arn    = var.target_group_arn
        weight = var.target_group_arn_weight
      }

      target_group {
        arn    = var.target_group_arn_green
        weight = var.target_group_arn_green_weight
      }
	  stickiness {
		enabled  = var.lb_sticky_enabled
		duration = var.lb_sticky_duration
	  }  
	}  
#    target_group_arn = var.target_group_arn
  }

  dynamic "condition" {
    for_each = length(var.service_path_pattern) > 0 ? [true] : []
    content {
      path_pattern {
        values = var.service_path_pattern
      }
    }
  }
  
tags = var.common_tags

}



resource "aws_lb_listener_rule" "static" {

  count    = var.static_action == true  ? 1 : 0

  listener_arn = var.lb_listener_arn
  priority     = var.priority


 action {
    type             = "forward"
    target_group_arn = var.target_group_arn
  }


  dynamic "condition" {
    for_each = length(var.service_path_pattern) > 0 ? [true] : []
    content {
      path_pattern {
        values = var.service_path_pattern
      }
    }
  }

  dynamic "condition" {
   for_each = length(var.service_host_header) > 0 ? [true] : []
    content {
	  host_header {
		values = var.service_host_header
      }
    }
  }	
  
  
  tags = var.common_tags
}

#resource "aws_lb_listener_rule" "ecs" {
#  count    = var.ecs_forward == true  ? 1 : 0  
#  
#  listener_arn = var.lb_listener_arn
#  
#  priority     = var.priority
#
# action {
#    type             = "forward"
#    target_group_arn = var.target_group_arn
#  }
#    
#  dynamic "condition" {
#    for_each = length(var.service_path_pattern) > 0 ? [true] : []
#    content {
#      path_pattern {
#        values = var.service_path_pattern
#      }
#    }
#  }
#  
#  condition {
#    host_header {
#      values = var.service_host_header
#    }
#  }
#  
#  tags = var.common_tags
#}
#