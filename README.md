# keip - Kubernetes Enterprise Integration Patterns

**The communication backbone for microservices, AI toolchains, and enterprise integration on Kubernetes.**

## What is keip?

keip (Kubernetes Enterprise Integration Patterns) is a Kubernetes operator that serves as the communication backbone for modern distributed systems. Whether you're orchestrating microservices, building AI toolchains, or handling traditional enterprise integration, keip transforms complex data flow challenges into simple, declarative configurations.

Instead of writing, compiling, and deploying Java applications for service communication and data integration, define Spring Integration routes as Kubernetes resources and let keip handle the rest.

### The Problems It Solves

Modern distributed systems often need to:
- **Microservices Communication**: Orchestrate complex service-to-service interactions, event streaming, and API workflows
- **AI Toolchain Coordination**: Connect AI models, data pipelines, feature stores, and inference engines in sophisticated workflows
- **Enterprise Integration**: Move data between different systems (databases, message queues, APIs, files)
- **Data Transformation**: Convert formats (JSON to XML, CSV to database records, etc.) and enrich data in transit
- **Smart Routing**: Route messages based on content, rules, or dynamic conditions
- **Resilient Operations**: Handle errors, retries, and circuit breaking gracefully
- **Dynamic Scaling**: Scale integration workloads based on demand
- **Legacy Systems**: Bridge legacy systems with modern cloud applications and microservices

Traditionally, this requires:
- Writing Java code with Spring Integration
- Managing application lifecycle and deployments
- Handling scaling and resilience manually
- Complex CI/CD pipelines for every integration change

### The keip Solution

With keip, you define your integration logic in XML configuration and deploy it as a Kubernetes resource. The operator automatically:
- Creates and manages the underlying Spring Boot application with Spring Integration
- Provides access to the entire Spring ecosystem (hundreds of connectors, components, and enterprise patterns)
- Handles Kubernetes deployment, scaling, and lifecycle
- Provides cloud-native resilience and observability
- Enables runtime route updates without code compilation

## Key Features

- **Kubernetes Native**: Fully integrates with Kubernetes using custom resources and scales with cluster capabilities
- **Spring Ecosystem Powered**: Built on Spring Boot and Spring Integration with access to 300+ connectors and enterprise patterns
- **No Code Compilation**: Define integration routes in XML and deploy instantly
- **Auto-Scaling**: Leverages Kubernetes scaling capabilities for integration workloads
- **Runtime Flexibility**: Update integration routes without rebuilding applications
- **Enterprise Ready**: Battle-tested Spring components with comprehensive error handling and monitoring
- **Cloud-Native Observability**: Native Kubernetes monitoring and logging support

## Quick Start

### Prerequisites

- Kubernetes cluster (v1.24+ recommended)
- `kubectl` installed and configured to interact with your cluster

### Installation

Choose one of the following methods:

**Option A — Static manifest (recommended):**
```bash
kubectl apply -f https://github.com/codice/keip/releases/latest/download/install.yaml
```

**Option B — Remote kustomize:**
```bash
kubectl apply -k 'https://github.com/codice/keip/operator?ref=main'
```

**Option C — From source (development):**
```bash
git clone https://github.com/codice/keip.git && cd keip/operator
make deploy
```

All methods create the `keip` and `metacontroller` namespaces and deploy the necessary components.

**Verify installation:**
```bash
# Check metacontroller pod
kubectl -n metacontroller get po

# Check keip webhook pod
kubectl -n keip get po
```

### Your First Integration Route

Create a simple integration that prints a message every 5 seconds:

1. **Create the integration configuration:**
   ```bash
   cat <<YAMEOF | kubectl create -f -
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: keip-route-xml
   data:
     integrationRoute.xml: |
       <?xml version="1.0" encoding="UTF-8"?>
       <beans xmlns="http://www.springframework.org/schema/beans"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xmlns:int="http://www.springframework.org/schema/integration"
              xsi:schemaLocation="http://www.springframework.org/schema/beans
                      https://www.springframework.org/schema/beans/spring-beans.xsd
                      http://www.springframework.org/schema/integration
                      https://www.springframework.org/schema/integration/spring-integration.xsd">

         <int:channel id="output"/>

         <int:inbound-channel-adapter channel="output" expression="Hello from keip every 5 seconds">
           <int:poller fixed-rate="5000"/>
         </int:inbound-channel-adapter>

         <int:logging-channel-adapter channel="output" log-full-message="true"/>
       </beans>
   YAMEOF
   ```

2. **Deploy the integration route:**
   ```bash
   cat <<YAMEOF | kubectl create -f -
   apiVersion: keip.codice.org/v1alpha2
   kind: IntegrationRoute
   metadata:
     name: example-route
   spec:
     routeConfigMap: keip-route-xml
   YAMEOF
   ```

3. **Check the status and view logs:**
   ```bash
   kubectl get ir
   kubectl logs -f deployment/example-route
   ```

4. **Clean up:**
   ```bash
   kubectl delete ir example-route
   kubectl delete cm keip-route-xml
   ```

## Advanced Configuration

### Custom Container Images

The default keip container provides basic Spring Integration components. For advanced use cases, you can create custom containers with additional Spring Boot starters, Spring Integration components, or your own Java libraries:

1. Copy the `keip-integration/` directory and update `groupId`, `artifactId`, and `version` in `pom.xml`
2. Add any Spring Boot starters or custom dependencies to `pom.xml`
3. Update the `keip-controller-props` ConfigMap to reference your custom image
4. Restart the webhook deployment

### Debugging

View operator logs for troubleshooting:
```bash
# Metacontroller logs
kubectl -n metacontroller logs -f sts/metacontroller

# Keip webhook logs
kubectl -n keip logs -f deployments/integrationroute-webhook
```

For verbose logging, set `LOG_LEVEL=DEBUG` in the webhook deployment.

## Examples

For more comprehensive examples including a secure HTTPS server and message routing with externalized configurations,
see the [operator/examples](operator/examples) directory.

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
