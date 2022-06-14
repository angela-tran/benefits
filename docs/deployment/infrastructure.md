# Infrastructure

The infrastructure is configured as code via [Terraform](https://www.terraform.io/), for [various reasons](https://techcommunity.microsoft.com/t5/fasttrack-for-azure/the-benefits-of-infrastructure-as-code/ba-p/2069350). All Azure resources under the `RG-CDT-PUB-VIP-CALITP-P-001` [resource group](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal) should be represented in this repository. The exception is secrets, such as values under [Key Vault](https://azure.microsoft.com/en-us/services/key-vault/) and [App Service application settings](https://docs.microsoft.com/en-us/azure/app-service/configure-common#configure-app-settings).

For browsing the [Azure portal](https://portal.azure.com), [switching your `Default subscription filter`](https://docs.microsoft.com/en-us/azure/azure-portal/set-preferences) to only `CDT/ODI Production` is recommended.

## Architecture

### System interconnections

```mermaid
flowchart LR
    dmv[DMV Eligibility Verification API]
    benefits[Benefits application]
    style benefits stroke-width:5px
    recaptcha[Google reCAPTCHA]
    rider((User's browser))

    rider --> benefits
    rider --> Login.gov
    rider --> recaptcha
    rider --> Littlepay
    rider --> Amplitude

    benefits <--> Login.gov
    benefits <--> recaptcha
    benefits --> dmv
    benefits --> Amplitude
    benefits <--> Littlepay
```

### Benefits application

```mermaid
flowchart LR
    internet[Public internet]
    WAF
    django[Django application]
    interconnections[Other system interconnections]

    internet --> Cloudflare
    Cloudflare --> WAF
    django <--> interconnections

    subgraph Azure
        WAF --> NGINX

        subgraph App Service
            subgraph Custom container
                direction TB
                NGINX --> django
            end
        end
    end
```

WAF: [Web Application Firewall](https://azure.microsoft.com/en-us/services/web-application-firewall/)

## Monitoring

We have [ping tests](https://docs.microsoft.com/en-us/azure/azure-monitor/app/monitor-web-app-availability) set up to notify about availability of the dev, test, and prod deployments. Alerts go to [#benefits-notify](https://cal-itp.slack.com/archives/C022HHSEE3F).

## Making changes

1. Get access to the Azure account through the DevSecOps team.
1. Install dependencies:
   - [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
   - [Terraform](https://www.terraform.io/downloads)
1. [Authenticate using the Azure CLI](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/azure_cli), specifying the `CDT/ODI Production` Subscription.
1. Outside the [dev container](../../getting-started/), navigate to the [`terraform/`][terraform-dir] directory.
1. [Initialize Terraform.](https://www.terraform.io/cli/commands/init)

   ```sh
   terraform init
   ```

1. Make changes to Terraform files.
1. [Plan](https://www.terraform.io/cli/commands/plan)/[apply](https://www.terraform.io/cli/commands/apply) the changes, as necessary.

   ```sh
   terraform apply
   ```

1. [Submit the changes via pull request.](../development/commits-branches-merging/) Be sure to specify whether they've been applied, i.e. whether they're live or not.

For Azure resources, you need to [ignore changes](https://www.terraform.io/language/meta-arguments/lifecycle#ignore_changes) to tags, since they are [automatically created by Azure Policy](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/tag-policies).

```hcl
lifecycle {
  ignore_changes = [tags]
}
```

[terraform-dir]: https://github.com/cal-itp/benefits/tree/dev/terraform