locals {

  # Tags
  common_tags = merge(var.tags, { CostOwnerTeam = var.CostOwnerTeam, SupportTeam = var.SupportTeam[var.env_type] })
 
 lambda_layers_app = {
   scheduled-1630 = [data.aws_lambda_layer_version.psycopg2_layer.arn]
   scheduled-ticket = [data.aws_lambda_layer_version.psycopg2_layer.arn]
   scheduled-change = [data.aws_lambda_layer_version.psycopg2_layer.arn,data.aws_lambda_layer_version.aiohttp_layer.arn]
   scheduled-knowledge = [data.aws_lambda_layer_version.psycopg2_layer.arn]
   bedrock-ticket = [data.aws_lambda_layer_version.psycopg2_layer.arn]
   bedrock-change =  [data.aws_lambda_layer_version.psycopg2_layer.arn,data.aws_lambda_layer_version.aiohttp_layer.arn]
   bedrock-knowledge =  [data.aws_lambda_layer_version.psycopg2_layer.arn,data.aws_lambda_layer_version.kb_layer.arn]
   bedrock-ticket = [data.aws_lambda_layer_version.psycopg2_layer.arn,data.aws_lambda_layer_version.aiohttp_layer.arn]
 
 }

lambda_secret = {
  scheduled-1630 =  { 
                      secret_name = "middlewareNodeSecret"
                      region_name = var.region
                    }
  scheduled-ticket =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }
  scheduled-change =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }                  
  scheduled-knowledge =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }
  bedrock-change =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }
  bedrock-knowledge =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }               
  bedrock-ticket =  { 
                      secret_name = "manual_lambda_secret"
                      region_name = var.region
                    }

}

}     ##### End of Locals

