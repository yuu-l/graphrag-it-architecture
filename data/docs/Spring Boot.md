## 特性

Spring Boot 是基于 Spring Framework 的应用框架，目标是简化 Spring 应用的创建、配置与运行。其核心能力包括自动配置、起步依赖和可执行 JAR。官方文档强调 Spring Boot 采用“约定优于配置”的方式，根据类路径中的依赖、配置属性以及已定义的 bean 自动配置 Spring 应用，从而减少手工编写 XML 或 Java 配置的工作量。

Spring Boot 提供生产就绪能力，例如通过 Spring Boot Actuator 暴露健康检查、指标、环境信息和审计端点，便于运维与监控。开发者还可以使用 Spring Boot DevTools 提升开发体验，获得应用自动重启、配置热加载和调试辅助等能力。

Spring Boot 支持外部化配置，可通过 properties 文件、YAML 文件、环境变量、命令行参数等方式提供配置。官方文档中详细说明了配置属性绑定和 profile 机制，使同一应用可以适配开发、测试、生产等不同环境。

## 适用场景

Spring Boot 适合构建独立运行的 Spring 应用，尤其是 Web 服务、REST API 和微服务。借助内嵌 Servlet 容器（如 Tomcat、Jetty 或 Undertow），应用可以直接通过 `java -jar` 启动，无需部署到外部应用服务器，这降低了微服务的部署与运维复杂度。

Spring Boot 也适合与 Spring 生态内其他项目集成，例如 Spring Data、Spring Security、Spring Batch、Spring Integration 和 Spring Cloud。官方文档中多处说明 Spring Boot 的自动配置和起步依赖能够简化这些技术的整合，因此适用于批处理任务、消息驱动应用、安全服务等场景。

此外，Spring Boot 适合云原生和容器化部署。其可执行 JAR、外部化配置和 Actuator 健康检查能力，使其便于在 Kubernetes、Cloud Foundry 等平台上运行。官方文档还提供了与 Docker、GraalVM native image 等部署目标相关的内容，适用于需要快速迭代和标准化交付的应用。

## 部署形态

Spring Boot 应用最常见的部署形态是可执行 JAR。通过 `spring-boot-maven-plugin` 或 `spring-boot-gradle-plugin` 打包出的 JAR 包含内嵌服务器和全部依赖，可直接使用 `java -jar` 命令运行，适合独立部署和容器镜像构建。

另一种部署形态是传统 WAR 包。Spring Boot 支持将应用打包为 WAR 文件并部署到外部 Servlet 容器，但需要将启动类继承 `SpringBootServletInitializer` 并做相应配置。这种形态适用于需要与企业现有应用服务器兼容的场景。

在云原生环境中，Spring Boot 应用通常被打包为 OCI 或容器镜像，部署到 Kubernetes、Cloud Foundry 等平台。官方文档介绍了与 Docker Compose、Kubernetes 的集成实践，包括通过 Actuator 提供就绪探针和存活探针，以便平台管理应用生命周期。Spring Boot 还支持 GraalVM native image 编译，生成独立可执行文件，以减少启动时间和内存占用，但该形态对反射、资源和动态代理等有一定限制。

## 局限

Spring Boot 的自动配置虽然减少了样板配置，但也可能使应用内部行为不够透明。当自动配置不符合预期或发生配置冲突时，开发者需要理解自动配置条件、排除特定配置类或手动定义 bean，这增加了排查复杂度。官方文档也建议通过 `--debug` 或 Actuator 的 `conditions` 端点查看自动配置报告。

起步依赖和默认配置可能导致应用引入比实际需要更多的依赖或默认行为。虽然官方提供了细粒度的依赖管理和排除机制，但团队仍需要关注依赖治理，避免无关依赖进入生产包，从而影响镜像体积、启动时间或攻击面。

Spring Boot 应用通常依赖 Spring Boot 与 Spring Framework 的版本配套关系。升级 Spring Boot 版本时，可能涉及配置属性变更、自动配置行为调整或第三方库兼容性问题。官方文档维护了版本升级说明，但复杂应用仍需要相应测试和迁移投入。对于需要极致控制启动时间、内存占用或运行时行为的场景，内嵌服务器和自动配置可能不如手工优化的轻量级方案灵活。