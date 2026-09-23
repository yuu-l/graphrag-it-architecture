## 特性

Nginx（官方文档中常写作 nginx）是一个高性能 HTTP 服务器、反向代理服务器、内容缓存和邮件代理服务器，也可通过 stream 模块提供 TCP/UDP 代理能力。官方文档描述其采用多进程结构：一个 master 进程负责读取配置、管理工作进程，worker 进程实际处理请求；nginx 使用事件驱动模型并依赖操作系统机制高效分发请求。

在 HTTP 场景中，Nginx 支持基于 server_name 和监听地址的虚拟主机，基于 location 的精确、前缀、正则等 URI 匹配，静态文件服务、自动索引、MIME 类型映射、Range 请求、gzip 压缩、TLS/SSL 终止、SNI、HTTP/2、实验性 HTTP/3 over QUIC、WebSocket 代理，以及 FastCGI、uWSGI、SCGI、memcached、gRPC 等协议代理。反向代理还支持响应缓存、请求限速、连接限速、访问控制、重写、子请求和自定义访问日志。

在负载均衡方面，Nginx 通过 upstream 定义后端服务器组，官方文档列出的负载均衡算法包括轮询、最少连接、IP 哈希、通用哈希和随机。Nginx 的模块化设计允许官方或第三方模块扩展，支持编译期静态包含以及运行时动态加载部分模块；配置可通过信号进行平滑重载和在线二进制升级。

## 适用场景

Nginx 适合作为静态内容 Web 服务器，用于前端静态资源、单页应用、图片、视频和文件下载等场景。它可以结合 gzip、缓存头、条件请求和 Range 支持，减少后端压力并提高传输效率。

Nginx 常用于反向代理和负载均衡入口，部署在多个后端应用实例之前，集中处理 TLS 终止、域名和 URI 路由、限流、访问控制、缓存与安全策略。官方文档中的 server_name、location、proxy_pass 和 upstream 组合能够覆盖从单体应用扩展到微服务 API 网关的多种需求，也常用于 Kubernetes Ingress Controller。

Nginx 还适用于 WebSocket 长连接代理、TCP/UDP 流代理和邮件代理。对于需要统一入口、多种后端协议并存或需要前置缓存与限流的架构，Nginx 可以作为轻量的边缘代理层。

## 部署形态

Nginx 支持在 Linux、BSD 等 Unix 类系统上通过源码编译或包管理器安装，官方文档提供源码构建和安装说明。传统主机部署由 systemd/init 等服务管理器管理，运行一个 master 进程和多个 worker 进程，主配置通常为 nginx.conf，并可通过 include 拆分多文件。

常见部署形态包括：单独作为静态资源服务器；作为应用集群前方的反向代理和负载均衡层；作为容器中的入口或 Sidecar，或通过 ingress-nginx 作为 Kubernetes Ingress 控制器；与云负载均衡、Keepalived 或 VIP 组合形成高可用入口。也可以部署为邮件代理或 TCP/UDP 代理。

配置变更通常先用 nginx -t 校验，再通过 nginx -s reload 或向 master 进程发送 HUP 信号实现平滑重载。官方文档还描述了通过 USR2、WINCH、QUIT 等信号进行在线二进制升级的方式，适合高可用生产环境。

## 局限

开源版 Nginx 配置是静态文件，修改后必须重载才生效，官方文档没有提供运行时动态配置 API 或图形化管理界面。尽管 reload 相对平滑，但对于高频、大规模或自动化动态路由变更，需要额外配置生成、服务发现或控制平面。

Nginx 本身不执行 PHP、Python、Java 等业务代码，必须通过 FastCGI、uWSGI、SCGI、HTTP 等协议代理到外部应用服务。它不是完整应用服务器，也不内置数据库、消息队列或业务框架。

开源版的健康检查主要为被动式，例如通过 max_fails 和 fail_timeout 识别上游失败；主动健康检查、高级仪表板、JWT/OpenID Connect 等能力通常属于商业版 NGINX Plus。此外，复杂 location、rewrite 和多 upstream 配置会增加维护成本，在大型集群中通常需要模板化和外部编排。