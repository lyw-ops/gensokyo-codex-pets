# 灵梦工作状态桌宠（源码与安装版边界）

## 当前开发：task_1/task_3/task_4/task_5 静态 + task_2 动态原生垂直切片（2026-09-20）

源码已将observer的 `WorkStatus.active` 传入 `PetBehavior`。当base为 `working`
且真实活动任务数恰为1时，选择`work_eating_task_1`静帧；恰为2时播放独立
`work_eating_task_2`身份的已审核16帧精确循环（10 fps）；恰为3、4时分别选择`work_eating_task_3`、
`work_eating_task_4`，5个及以上通过同一封顶策略选择`work_eating_task_5`。后三者按原字节
显示对应的Eating Set v1单帧，没有已审核多帧或分层源，因此是诚实静态姿态，不是动画
完成声明。
普通数量变化在循环边界切换，高优先状态和交互立即抢占，reduced motion固定frame 0。

Tier1用`--work-tier-1 pets/reimu/animations/eating/sources/task_1-static-v1`。构建时用
`--work-tier-2 pets/reimu/animations/eating/sources/task_2-chew-v9`
、`--work-tier-3 pets/reimu/animations/eating/sources/task_3-static-v1`和
`--work-tier-4 pets/reimu/animations/eating/sources/task_4-static-v1`显式打包资源。
Tier5预览另加`--work-tier-5 pets/reimu/animations/eating/sources/task_5-static-v1`。
原生加载器校验manifest身份、摘要、帧数、FPS、序号和每帧摘要；破损或缺失时只降级
对应档位。task_2隔离预览已获用户确认；用户于2026-09-20分别确认了task_1、task_3、
task_4和task_5原生审阅图，因此所有五档现可用于正式身份构建。这些批准只覆盖已展示的
单帧大小、姿态、静态保持与运行时切换，不把task_1、task_3、task_4或task_5记作多帧
动画完成。
五个工作餐档位都尚未安装，既有批准也没有安装正式身份应用。
task_5视觉门已关闭，但尚未安装；它同样不是多帧动画。现有安装版未改变。
task_1视觉门也已关闭，但尚未安装；它同样不是多帧动画。
进入/离开task_2、未来跨档和抢占恢复的过渡动画是独立后续任务；它们不得延迟高优先抢占
或恢复过期档位。当前正式安装版仍以 `HANDOFF.md` 顶部的安装回执为准。

## 当前版本：1.7 单一合并应用 + 行为日志（2026-09-07）

用户要求「留下一个，将他们的功能合并」，因此预览身份已并回安装身份：
`/Users/lyuyuwei/Applications/灵梦桌宠.app`，**1.7 / build 9**，
bundle ID `local.reimu.onigiri.desktop`，可执行文件 SHA-256 `8f05abc9efa2ec1d…`。
构建记录在 `~/.codex/artifacts/reimu-unified-20260907/`，与安装副本逐字节相同。
其余 17 个历史包移入 `~/.codex/artifacts/reimu-app-archive-20260907/`，未删除任何文件；
`manifest.json` 记录来源与摘要，`scripts/restore.sh` 可按原路径还原。

1.0 → 1.7 是同一份源码的线性演进，旧包没有 1.7 缺少的功能；1.3 的「工作中无限吃饭」
此前已由用户批准的站姿默认与有限挂机吃饭取代，本轮未恢复。行为规则本身未改。
资源与已批准 1.6 预览逐字节相同，是 1.3 资源的严格超集，本轮无新美术。

新增只读观察：`PetBehavior.onTrace`（默认 nil）与 `PetLog` 把 base 变化、动作起止与原因、
真实 `meal_attempt`（roll／命中／重试间隔）、门禁、工作快照与用户输入写成逐行 JSON
到 `~/Library/Logs/ReimuPet/behavior.jsonl`（1 MiB 上限、一代轮转）。
`--behavior-log PATH` 改路径，`--no-behavior-log` 关闭，QA 模式不写真实日志。
右键菜单多了真实挂机倒计时与「在 Finder 中显示行为日志」；
**打开菜单本身会重置 60 秒安静计时**，所以日志才是不打扰的观察方式。
监控脚本 Harness `build/reimu-unified-monitoring-20260907-v1/watch.py` 只读采样，
写 `~/Library/Logs/ReimuPet/watch-summary.json`。

84 项行为、29 项原生、28 项状态、3 项表情、5 项站姿检查通过；三方状态评估 48 次零分歧。
真实事件探针结论：`working`／`round_ended`／`interrupted`／`closed` 已被真实事件驱动，
**`needs_input` 与 `failed` 从未被真实事件驱动**（需 PermissionRequest／Notification／
Elicitation 与 StopFailure，至今 0 行）；未制造任何事件。真实随机挂机体感仍在采集。

## 历史预览：1.6 有限挂机吃饭（2026-09-07，已并入 1.7）

最终包：`~/.codex/artifacts/reimu-native-idle-meal-20260907-final/灵梦桌宠预览.app`，
**1.6/build 8**，已启动；同日无 `-final` 后缀的是保留中间构建。安装版 1.3 不变。
用户已确认 8142 默认 cut、大小／位置和 8 秒时长，并授权此接入。

真实 idle 安静 60 秒后首次尝试，25% 概率吃饭，未命中等 30–45 秒；每餐播两轮共8秒。
结束／打断后自动餐冷却至少180秒，互动后至少60秒安静；不补播错过的尝试。
冷却只在进程内保存；重新启动仍须60秒新闲置。工作、轮次结束、未知和等待不自动吃饭。
右键主动喂食仍4秒，四连击生气仍1.2秒，失败、暂停、减弱动态、拖动、休眠恢复保留。
菜单打开、鼠标按住、素材降级均阻止自动吃饭。状态接收器和任务数不由动作修改。

原始 688 坐姿在596参照画布以482方图等比显示，位置沿用批准的 Harness placement；
人物 alpha 命中检测使用同一个绘制矩形。站姿原1254方图与三张眼姿原字节保留。
是对齐直接换图，不是新起坐绘画；AppKit 与 Pillow 采样边缘不声明逐像素一致。

66项行为、25项原生、28项状态、3项表情、5项站姿检查通过；源图／安装版／旧1.5包
保持原摘要，启动后严格验签通过。真实随机挂机的日常体感仍供用户查看，不安排监控。
复现命令、签名注意事项、证据与下一次提示词见 Harness
`build/reimu-native-idle-meal-20260907-v1/README.md` 及两仓交接顶部。

## 历史预览：1.5 站姿默认待机（2026-09-07）

当前可运行包：`~/.codex/artifacts/reimu-native-standing-20260907/灵梦桌宠预览.app`，
1.5/build 7；保留安装版 1.3 和旧预览 1.4.1。用户已单独确认站姿眨眼，原生组合留供查看。

默认站姿与真实工作卡片独立。工作中、闲置和轮次结束采用 7 秒一次的原 250 ms 眨眼；
等待、失败、未知等保持原睁眼站姿。单击／双击只切换站姿眼部；拖动和放下保持站姿。
右键喂食仍播一次已审核 4 秒坐姿片段，结束回到最新状态的站姿；四连击生气保留原
坐姿表情和 1.2 秒保持。失败优先、冷却、暂停和减弱动态保留，图片 alpha 命中随姿势切换。
工作中无限吃饭与旧自主咀嚼暂停已移除；自动挂机吃饭、起坐过程和脚底共用锚点待后续。
当前两种姿势直接切换，没有新的起坐绘画。接收器和真实状态／数量完全独立。

构建现在必须提供 `--standing NEW_STANDING_PACKAGE`。先用现有 Pillow 环境运行
`desktop/macos/import_standing.py --harness-root HARNESS_ROOT --source APPROVED_FINAL
--reduced-source APPROVED_REDUCED_FINAL --out NEW_PACKAGE`；工具通过 Harness 公共 CLI
验证并核对所有已确认帧，按原字节去重打包三张姿势。完整路径命令见 Harness
`build/reimu-native-standing-20260907-v1/README.md`。随后执行原 `build.py` 命令并增加
`--standing NEW_PACKAGE --preview`，输出到 `.codex/artifacts` 新应用目录。
运行时校验摘要；坏眼姿／清单显示带菜单提示的原站姿，原基准丢失则拒绝启动。
`--standing-root DIR` 与 `test_standing.py BINARY` 仅供隔离素材 QA，不用于真实状态模拟。

37 项行为、23 项原生、28 项状态、3 项生气和 5 项站姿素材检查通过。CUA 查看站姿、
展开紧凑卡片、右键喂食和回站姿；真实数量前后保持 2 项。启动后严格验签通过。
没有安装替换或重新验证 Claude 连接。以下内容为旧版本历史，当前状态以本节及 HANDOFF 为准。

## 历史预览：1.4.1 紧凑状态框（2026-09-07）

用户反馈状态栏过大后，当前包改为
`~/.codex/artifacts/reimu-compact-status-20260907/灵梦桌宠预览.app`。
160/240/320/400 px 人物对应 208/240/280/280 pt 框宽；卡片高 60 pt、箭头 28 pt、
整体高 96 pt，字体 14/12 pt。它沿用预览版的独立偏好，安装的 1.3 继续保留。
20 项原生检查通过，展开／收起、屏幕边缘处理及真实状态含义不变。

用户本轮通知 Claude 可以连接，已恢复连接验证。现有钩子配置与接收器一致；
日志已收到近期真实的开始、16 对工具开始／返回与结束事件。不需要重装钩子或
发送新任务；此结论不等于所有审批／失败／重连分支都已实际验证。详情见最新 HANDOFF
和 Harness `build/reimu-compact-status-claude-20260907/qa/`。下面 1.4 为保留的历史版本说明。

## 最新开发：1.4 原生状态框独立预览（2026-09-07）

已安装应用仍为 1.3。当前源码可构建 1.4；本轮仅用 `build.py --preview`
生成独立的「灵梦桌宠预览」，bundle ID 为 `local.reimu.onigiri.preview`，位置、
大小及折叠偏好与已安装应用分开。当前可查看的构建在
`~/.codex/artifacts/reimu-native-status-bubble-20260907/灵梦桌宠预览.app`。
Harness `build/reimu-native-status-bubble-20260907-v1/` 保存记录与 QA。

- `StatusBubble.swift` 在独立透明浮窗中显示两行深色胶囊框；替代原来覆盖人物脚边的
  工作状态小条，互动回应文字仍保留。36 pt 箭头按钮和右键菜单均可展开／收起。
- 框体跟随人物位置，优先放在下方，空间不足时放到上方或侧面并限制在屏幕内。
  收起后窗口缩到按钮大小，人物和按钮锚点不变；透明角落与空隙按形状进行鼠标穿透。
  极小屏幕上可能没有足够的互不重叠空间，仍优先保证控件留在屏内。
- 复用原有只读工作快照；显示通用的来源标题、真实状态／活动数量，以及其他未知任务
  提示。没有任务名或具体操作来源时不会编造它们。折叠状态独立保存，不取消角色动作。
- 右键喂食、点击／连击、生气、暂停、减弱动态和现有调度保持原行为。
  「站姿默认、吃饭作为挂机活动」仍是下一步素材衔接与调度工作，本预览尚未切换。

本轮验证：30 项行为检查、28 项状态约定、3 项表情素材检查、最终构建 19 项原生
窗口／菜单／计时器检查（含 27 种框体屏幕位置）；仓库检查通过。CUA 实际展开／收起，
观察真实数量从 2 变为 1，并选择 160 px 人物检查。物理拖动手感仍属人工检查范围。
当前预览仅复用已审核吃饭素材，未导入待确认站姿；没有恢复 Claude 验证。

构建脚本只对新输出清除不兼容签名的 FinderInfo／ResourceFork 元数据，再做本地签名
和严格验证；不清理来源或移除其他扩展属性。本机 Documents 内的 `.app` 在启动后
再次出现 FinderInfo 和 FileProvider 标记，复查签名失败；因此可运行包放在上述本机
构建目录。Harness build 中两份旧应用仅保留诊断，不作为当前可用包。
其余使用与 1.3 历史说明如下。

本目录提供独立 macOS AppKit 桌宠和被动工作事件接收器。它复用用户已确认的
40 帧吃饭团/眨眼示例，收到工作事件后切换播放；不会控制 Codex 或 Claude，
不会代替用户审批，也不会发送对话。非官方东方同人，仅作本地示例。
源码与接入协议在 Consumer；Sprite Harness core 保持 provider-neutral。

## 1.3 交互

- 单击人物：眨眼并短暂回应「嗯？」。
- 双击：连续眨眼，回应「戳到啦」。
- 快速连续四次点击：保持皱眉表情 1.2 秒，出现红色怒气符号和「むっ！」，回应「让我吃完嘛」；锁定和冷却期间不堆积动作。
- 右键「喂一口饭团」：原 40 帧只播放一轮，随后恢复当前工作状态。
- 拖动达到 4 pt 后才作为拖拽；轻点不挪位置。拖动时保持坐姿静帧，放下后短暂停留，
  回到最新工作状态。不是新绘制的飞行/落地动作。
- 工作中偶尔短暂停下咀嚼，至少间隔 90 秒；自主尝试间隔为 20–45 秒，大多数不触发。

交互状态机与任务数量分开。任务数量变化不会重启动作；交互中途工作状态变化，
结束时返回最新的状态。失败状态优先。暂停/减弱动态仍有效；减弱动态中的点击保留
文字反馈而不播放帧。悬浮反馈文字不会覆盖原来的工作状态说明。

回应/双击仍复用原来的眼睛帧；不耐烦已接入用户确认的皱眉、怒气符号和日文透明姿势。
新姿势是眉眼局部补丁加独立符号，衣服、饭团及饰品遮挡保留原图像素。
没有新增抬头、举御札、飞行或趴桌睡觉素材。完整 35 动作登记表仍是设计规格；
角色睡眠链、视线追踪、六档食物视觉尚未实现。系统休眠暂停播放器不是角色睡眠动作。

纯状态机测试：`/usr/bin/python3 desktop/macos/test_behavior.py`（30 项）。
实际原生 UI 已验证单击、双击、四连击、喂食，以及恢复真实工作状态。
物理拖动 CUA 返回 `AXError.notImplemented`；拖拽状态机和原生位移/边界有程序化验证，
物理体验仍需人工检查。

## 使用

本机应用：`~/Applications/灵梦桌宠.app`，桌面「灵梦」文件夹内有快捷方式。
右键可查看两个事件源是否曾收到事件，以及暂停、减弱动态、大小和退出菜单。
“已收到事件”仅表示接收过该来源的钩子，不表示已覆盖应用全部任务。

安装接收器（先不加 `--apply` 可检查目标路径）：

```sh
/usr/bin/python3 desktop/bridge/install.py --apply
```

它将脚本放入 `~/Library/Application Support/ReimuCompanion/`，合并
`~/.codex/hooks.json` 和 `~/.claude/settings.json`，保留其他设置及已有钩子。
原内容备份在接收器目录下的 `backups/<timestamp>/`；安装不会更改钩子信任。
Codex 自定义 `CODEX_HOME`、Claude 自定义配置目录和远程 Code 环境尚未支持。

Codex：打开终端运行 `/Applications/ChatGPT.app/Contents/Resources/codex`，
输入 `/hooks`，由用户信任命令中包含 `ReimuCompanion/observer.py` 的新钩子。
随后启动新一轮工作验证。绝不能使用绕过钩子信任的参数或直接修改信任记录。
Claude：本机 Claude 桌面 Code 使用本地用户 hooks 配置；更改后从新会话验证，
不要以单独运行 CLI 时的登录状态推断桌面 Code 的登录状态。

## 状态含义与边界

| 收到的事件/情况 | 桌宠显示与动作 |
| --- | --- |
| UserPromptSubmit、工具开始/返回 | 工作中；原 40 帧、10 fps、4 秒循环 |
| PermissionRequest、支持的输入请求 | 等待输入或审批；静止 |
| Stop | 这一轮已结束；30 秒后回到观察到的闲置状态 |
| Interrupt | 已中断；不会称为成功 |
| Claude StopFailure | 本轮遇到错误；普通工具错误仍可能恢复 |
| 已观察的闲置会话 | 大部分时间停留，约 7 秒眨眼一次 |
| 工作/等待状态 10 分钟没有新事件 | 状态待确认，不能推断完成或零任务 |
| 从未收到事件/坏快照 | 尚未收到事件/状态待确认 |

轮询间隔 1 秒。按 provider + 会话 ID 去重，仅计算已观察到的主会话；子代理事件单列，
不会抬高主任务计数。提供 turn_id 时拒绝旧轮次的延迟结束事件；Claude 常见钩子没有
turn_id，依赖同步短钩子和终止状态保护，不声称任意并发事件的全局有序性。
等待、失败、结束、中断不计入运行数。该计数不是所有应用任务的完整盘点。

观察器只输出未封顶的活动数量，不实现食物档位映射。现有
`app/task-state-mapping.js` 仍是唯一档位策略；本例尚未接入六档食物视觉。
完整 35 动作和睡眠链仍是后续阶段；本版已加入上述交互 FSM 与有限的自主停顿，视觉包括原吃饭/眨眼及新的生气静态姿势。
原 Codex 自定义宠物包仍保留，独立桌宠不会自动切换或关闭它。

## 数据与失败行为

JSON stdin 只提取事件名、provider、接收时间和散列后的会话/轮次/子代理 ID；
不保存 prompt、路径、对话、工具参数或输出。SQLite 文件为 600 权限，元数据限制为
256 会话和最近 2048 事件；子代理记录按时间清理。快照在数据库写锁内原子替换。
观察器遇到坏输入或不可写目录仍返回 `{}`、退出 0；不返回权限决定或继续运行指令。
观察失败可能丢失事件，此时桌宠通过超时退到未知；它不是审计或任务成功证明系统。

## 构建与检查

`macos/build.py --source SOURCE --icon ICON --annoyed ANGRY_PNG --standing STANDING_PACKAGE --out NEW_APP` 使用 Swift、AppKit、
CryptoKit 和本机 ad-hoc 签名构建 Apple Silicon / macOS 13+ 应用。
SOURCE 必须是当前明确钉住摘要的已审核示例（source.json SHA-256
`e622ed0123ece85248f82d2b08476e03a81c2e0eeb2e32304834d679f7457da8`）；
本目录不包含第三方图像，不是通用图片导入器，也不从预览 build 目录读取运行素材。
安装包携带已验证的帧副本，启动时重新校验摘要。
`--annoyed` 必须是用户确认的 `angry-final.png`，SHA-256 为
`314f34dcb6d5dbba04555f5996ec3f612e0dc65e7f0c080a027eee1093ccbd3f`。
它独立复制到 Resources/Reactions，不修改原 40 帧清单。运行时摘要不符或缺失时，
仅停用新表情、保留文字反馈并在菜单明确提示；吃饭/眨眼继续工作。
`test_reaction.py BINARY` 检查正常、缺失和损坏素材；`--reaction-root DIR` 仅用于隔离诊断。

```sh
/usr/bin/python3 -B -m unittest discover -s desktop/bridge -p 'test_*.py' -v
# 使用已构建的原生二进制检查 Python/Swift 状态约定：
/usr/bin/python3 desktop/macos/test_status.py "$HOME/Applications/灵梦桌宠.app/Contents/MacOS/ReimuPet"
```

原生诊断还支持 `--validate-assets`、`--status-snapshot FILE --at UNIX_TIME`，以及
隔离 QA 的 `--self-test --qa-domain UNIQUE_NAME --qa-report FILE`。
`--work-state-path FILE` 只用于隔离模拟测试；实际运行必须不带该参数。
检查报告和本机验证边界见根目录 HANDOFF。模拟事件通过不等于真实 provider 接入成功。

## 回退

本次 1.3 更新前的 1.2 应用保存在
`~/.codex/artifacts/reimu-anger-20260906/previous/灵梦桌宠.app`；
钩子配置和已确认信任完全未改。恢复 1.2 只需退出桌宠并复制该备份回原安装位置。
更早的 1.1 备份仍在 `~/.codex/artifacts/reimu-interaction-20260906/previous/`。

先从桌宠右键菜单退出。在两份 hooks 配置中只删除 command 指向上述 observer.py 的
hook 项，保留其他 hooks/settings；不要用旧备份覆盖后来新增的用户设置。
确认接收器不再被调用后，可归档其整个目录。本次安装前 1.0 应用完整备份在
`~/.codex/artifacts/reimu-work-observer-20260906/previous/灵梦桌宠.app`；可复制回
`~/Applications/` 恢复旧播放器，桌面快捷方式仍指向同一安装位置。

## 接口依据（2026-09-06）

- [OpenAI 官方 Codex hooks 文档](https://learn.chatgpt.com/docs/hooks)：事件、用户配置与手动信任。
- [Anthropic 官方 Claude Code hooks 文档](https://code.claude.com/docs/en/hooks)：桌面 Code 支持和事件语义。
- 本机实现证据：Codex CLI 0.153.4、Claude 桌面所附 Code 2.1.260。
  本版没有解析私有会话历史，也没有通过另起 app-server 假定能观察桌面所有任务。
