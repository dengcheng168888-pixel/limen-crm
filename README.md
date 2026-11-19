# Li-Men Technology CRM — 服务器版 V2.0

## 交付边界

这是可部署的中文工作台源码及完整开源 CRM 的官方安装入口，不是离线 HTML 或已开通的在线服务。中文工作台使用 FastAPI + SQLite、服务器会话登录、数据持久化、历史快照、客户看板、截图、渠道归因、入站 webhook、人工审核回传、AI 文本辅助。适合先在现有服务器小规模测试。当前只支持一个管理员账户，未做团队 RBAC、SSO、数据库横向扩展、静态数据加密或完整的报价/发票/ERP 功能；完整 Chatwoot 和 Frappe CRM 可分别提供消息接待及正式团队销售能力。它们各自独立安装，本包不宣称已实现两者双向同步或统一登录。没有 Docker 实际运行环境，应用功能通过本地运行验证；上游容器和真实外部平台需实际安装及验收。程序未进行第三方安全审计。

## 1. 最省钱的安装

现有 Linux VPS（Ubuntu/Debian 等）即可，前提是已经有 Docker Engine + Compose、Python 3、HTTPS 域名、足够的内存及硬盘。先运行 `free -h; nproc; df -h; sudo ss -lntp` 查看资源/端口。不要覆盖网站、代理、现有数据库、VPN。若只运行中文工作台，资源需求较低；完整 Chatwoot + Frappe + n8n 需要明显更多资源（建议测试环境从 4 vCPU/8GB RAM 考虑，实际以监控为准，不保证足够；完整系统可能需要 16GB 或更多）。

1. 把 ZIP 上传至服务器，解压后进入 `limen-crm-server`。
2. 执行 `./setup.sh`，自动生成强随机密码及接口密钥（不覆盖已有 .env）。
3. `docker compose ps` 和 `curl http://127.0.0.1:8780/health` 检查运行。
4. 在现有 HTTPS 反向代理添加 CRM 子域名（建议 `crm.koigatetech.com`；只是建议，需由你配置 DNS、证书）。示例 Caddyfile 在本包内。若使用 Nginx，反向代理至 `127.0.0.1:8780`，上传限制约 12MB。只允许 HTTPS 公网访问；不要把数据库端口或 .env 暴露在公网。`CRM_SECURE_COOKIE=1` 必须保留用于 HTTPS。若仅需本地调试可临时改为 0，不适用于公网。
5. 打开实际配置的 HTTPS 地址，管理员密码在服务器 `.env` 中。不要把密钥发给聊天或其他人。确认手机 Safari 与电脑 Chrome 都能登录、保存和重新打开。
6. `./backup.sh` 备份 SQLite 数据，另行加密保存 `.env`（含凭据）。首次测试用虚构客户；真实数据接入前测试恢复流程、磁盘空间和安全设置。

## 2. 完整开源系统

- Chatwoot：`CHATWOOT_URL=https://你的消息子域名 ./upstream/chatwoot-install.sh` 下载官方生产文件，人工核对后执行脚本提示的命令。此脚本**不启动容器、不改已有代理**。官方：https://www.chatwoot.com/deploy 。建议将 Web 端仅绑定 localhost 并使用现有 HTTPS 反代；数据库和 Redis 不应对公网开放。完成管理员初始化再接入 WA/FB/IG/TikTok/Email/网站客服；具体渠道取决于版本、账号资格、审批与社区版许可。
- Frappe CRM：官方生产安装说明 https://docs.frappe.io/crm/introduction/installation 。脚本 `upstream/frappe-install.sh` 使用官方 stable 镜像和 easy-install；可能占用 80/443，绝不能在运行现有网站的服务器盲目执行。先检查端口、DNS 和备份，确认可独占的主机或按官方 frappe_docker 自定义代理方案安装。正式 Frappe 管理销售、角色、任务、线索与机会；所有状态映射需要按实际站点验证。设置 `FRAPPE_URL` 仅添加入口，不实现双向同步。避免两个系统每日重复维护同一客户资料，正式使用时选定主数据系统。
- n8n：可选，官方自托管文档 https://docs.n8n.io/hosting/ 。设置 `N8N_URL` 仅为工作流入口；可配置审核后的回传 relay，不默认启动或收费。不要用不明确的许可证描述它为 OSI 开源。

编辑 `.env` 后 `docker compose up -d --force-recreate` 生效。平台 API、AI、存储、网络等费用由相应服务提供商确定；本包没有创建付费资源。

## 3. 网站询盘与广告来源字段

网站**服务端**在已有表单验证成功后，通过 HTTPS POST `/webhooks/leads`，Authorization: Bearer <CRM_INGEST_TOKEN>。事件 ID 必须是站点提交的稳定唯一 ID，重复推送同一 ID 不会重复入库。不要把 token 放在前端。示例见 `website-webhook-example.py`。

JSON 示例（虚构数据）：

```json
{"event_id":"site-test-001","name":"示例客户","company":"Example Water","phone":"+15550101000","email":"example@example.invalid","country":"","source":"TikTok 广告","channel":"网站表单","product":"M09","quantity":"200","ttclid":"TEST-ONLY","landing":"https://koigatetech.com/","utm":"utm_source=tiktok","message":"测试询盘"}
```

来源、产品、国家等未知时留空/待确认。新客户质量和确认状态默认待确认。采用号码、邮箱及 Chatwoot 账号/联系人 ID 去重；同名公司提示核实，避免盲目合并。Website, TikTok lead integration and Google via a trusted server/n8n normalize into the same API; TikTok 广告表单 Webhook 的验证/lead retrieval 需按账号配置完成，不是自动抓取。首次来源不随新消息自动改写，新互动 ID 存在消息记录中。

## 4. Chatwoot 消息

在 Chatwoot 设置 -> 集成 -> Webhook 创建 `https://你的CRM域名/webhooks/chatwoot`，订阅 `message_created`，将 Chatwoot 给出的签名密钥写入 `.env` 的 `CHATWOOT_WEBHOOK_SECRET`。该接收端按照 X-Chatwoot-Signature 和 Timestamp 的 HMAC-SHA256 校验并做 5 分钟重放保护；消息唯一 ID 幂等处理。仅接收已验证的客户入站消息，自动保存客户和文字沟通，若 payload 有 `ctwa_clid` 则保留，不凭此猜测是 FB 还是 IG。回复及完整附件请前往 Chatwoot 对话。没有同步旧消息、出站消息、附件或扫码内置浏览器。官方说明：https://www.chatwoot.com/hc/user-guide/articles/1677693021-how-to-use-webhooks 。

## 5. 广告回传

默认 `CRM_LIVE_POSTBACK=0`，界面仅生成有唯一键的审核队列，示例数据禁止真实发送。只对人工确认且已获授权的有效 B2B 线索和符合条件的真实收款生成事件。成交必须有独立付款编号和金额（USD）。不要把同一业务事件从多个系统反复发送；系统生成稳定 event_id。实际回传需在平台测试数据中验收后启用。发送异常状态为待核实，不盲目重试。

- Meta CTWA：`META_DATASET_ID`, `META_PAGE_ID`, `META_GRAPH_VERSION`, `META_ACCESS_TOKEN`, `META_LEAD_EVENT` 必须为实际账号支持的事件映射与参数，必要时配置 `META_TEST_EVENT_CODE`。采用 business_messaging + whatsapp + ctwa_clid + page_id 的接口格式；实际版本、WABA/dataset 和事件权限仍需 Meta 确认。参考 https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging/ 。
- TikTok Instant Form：`TIKTOK_EVENT_SET_ID`, `TIKTOK_ACCESS_TOKEN`, `TIKTOK_LEAD_EVENT`, `TIKTOK_PURCHASE_EVENT` 均需按事件管理工具映射；可配置测试代码。后端实现 CRM event set + lead_id 路径，需以广告账户导出的 payload 验证。参考 https://ads.tiktok.com/resources/help/article/how-to-postback-signals-through-events-api?lang=zh 。
- Meta 网站 fbclid、TikTok 网站 ttclid、Google gclid：保存真实 ID 和待审核事件，实际发送需独立、已审核的 HTTPS `AD_RELAY_URL` / `AD_RELAY_TOKEN` 工作流，按各平台网站或离线转化 API 要求构造 payload；本包没有自动完成这些工作流。状态“工作流已接收”不等于广告平台回传或归因成功。
- “API 已接收”仅说明 API 返回接受，不代表已归因、优化已生效或有效询盘增加。请到各平台 Events Manager 确认。事件时间需真实且在平台窗口内。严禁用虚构 ID 或成交金额打广告信号。

## 6. AI 辅助

配置 OPENAI_API_KEY 和 OPENAI_MODEL，提供翻译、中文客户需求分析、回复草稿；不会自动发送或写入客户档案。调用为真实付费 API（视账号而定），需获得适当的数据处理权限；不要输入不必要的个人信息。没有截图 OCR、产品知识库和自动发送，技术规格必须人工核实。

## 7. 验收及限制

数据库用 SQLite 单管理员并发乐观锁，写入时如新询盘或另一设备修改提示刷新，避免覆盖。全量状态与 audit 快照适合小规模测试，当前 API 单次 12MB，上限 10,000 项，各截图小于 1MB；大量客户与图片需迁移到 PostgreSQL 和对象存储，正式使用前需要升级至按记录 API、团队权限及自动备份。审核日志不是不可篡改的合规审计。不要将本包视为已达到出海吧所有商业功能。需要真实域名/现有 VPS 的 SSH 或控制台授权才能实际部署，本包没有访问现有服务器和网站。

## 从 Git 部署 CRM 服务端到 Railway

将本目录的内容提交到私有仓库，或在 Railway 将服务的 Root Directory 设置为包含 Dockerfile 的子目录。为 CRM 单独创建服务，连接该仓库，并在 /app/data 挂载持久卷。数据库采用 SQLite，服务使用单实例。容器默认以 UID/GID 10001 运行，挂载目录需要允许该用户写入。

在服务变量中设置 CRM_ADMIN_PASSWORD（至少 16 字符）、CRM_SESSION_SECRET 和 CRM_INGEST_TOKEN（各至少 32 字符，分别随机生成）。保留 CRM_SECURE_COOKIE=1，使用 HTTPS 登录。平台指定 PORT 时自动使用该端口，本地 Compose 默认使用 8780。上线后先用测试客户验证登录、跟进记录和重新部署后的数据留存。Chatwoot 和广告账户可以后续单独接入。
