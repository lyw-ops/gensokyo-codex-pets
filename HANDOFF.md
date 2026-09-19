# GPT project handoff / GPT 项目交接

## 2026-09-19 工作吃饭六档、挂机饭团与独立抓取动作已写入设计

用户重新确认最初核心设定：工作时灵梦持续吃饭，`ReimuFoodTier = min(activeTaskCount, 5)`
决定六格参考图中的餐食与情绪；这覆盖任何把工作默认改为站立、或把吃饭仅视为挂机动作的后续表述。
六格仍按 `idle, task_1, ..., task_5` 排列：0任务无工作餐，1任务单饭团含泪，2任务饭团+茶并缓和，
3任务米饭小菜且满足，4任务拉面/饺子且开心，5+为封顶宴席并喜极而泣。档位只在安全循环边界换组合，
不重启FSM；任务真值仍只来自observer/任务卡片，动画不改任务数。

另冻结两个扩展语义：`idle_onigiri` 是tier 0空闲时的有限挂机饭团，使用中性/满足表情，不复用task_1
含泪语义；手动喂食可共享核心clip，但触发、冷却、日志与中断原因独立。`drag_float` 是原生独立“被抓起”
held动作：不带桌子/榻榻米/食物，脚离地，衣袖/长发/裙摆/蝴蝶结有轻微下垂，只允许小幅滞后晃动，
不得复用自愿左右飞行；松手经`drag_land`回最新base，不能恢复拖动前的过期档位。

权威细节已写入`docs/reimu-action-system.md`，机器可读项同步到`pets/reimu/metadata/actions.json`，
参考图用途补入`docs/reference/reimu/eating_set_v1/README.md`。本条设计修改自身没有新绘图、Harness产物、
运行时代码、安装或视觉批准；维护者随后明确要求把当前累积工作区作为一个完整、可追溯快照提交并推送。
下方历史条目中的“当轮未提交／未推送”仍是各轮当时的事实，不应反向理解为当时已经发布。

发布前`actions.json`解析通过，37个`actionId`全部唯一且关键五项齐全；全树`git diff --check`、
`scripts/check-repository.sh`、125项工具测试（9项因consumer环境无Harness CLI而明确跳过）、14项bridge测试
与150项Swift行为检查通过。敏感凭证扫描无命中；没有安装或修改依赖。这里证明的是当前源码／素材快照
通过本地门禁，不等于被跳过的Harness集成测试、真实provider连接、安装包替换或新增动作视觉批准。

## 2026-09-17 睡眠短链固定背景修复及原生预览完成

本条覆盖上一版桌面稳定门禁失败状态。最终交付位于Harness `build/sleep-chain-stable-v2/`：
`preview.gif`、`review-sheet.png`、`睡眠短链预览.zip`、`release/`与qa/；其他reel/locked/final/stable为已否决中间实验，不用于后续。

- 不生成新脸或改变已确认sleep源；使用上轮imagegen四个关键帧和人工显式上/下场景合成。
  y<690来自关键帧，690–719为30px线性过渡带，y>=720完整复制选定睡姿；桌面/榻榻米位于固定区域。
  这是完整场景替换面板，不是自动分离头/手臂骨架。原始文件未修改；处理脚本prepare.py保留。
  早期内部面板有脸缘重影、硬切有发梢接缝，均未采用。最终仅下半场景锁定，不声称头部轮廓/所有袖子逐像素不变。
- verify.py检查60帧：替换区域外变化0；y>=720变化0（含RGBA）；sleep帧等于选定原图在透明底的合成；
  三个动态表情的RGB变化必须存在，防止把全静态误判成功。reduced60帧全部等于第一帧awake。
  Harness full/reduced校验通过，仍保留原图alpha=1散点的CONTENT_TOUCHES_EDGE，不声称零警告。
  查看过放大awake图与160px联系表；新动态神情/节奏尚待用户视觉确认。
- consumer新增preview-only `--sleep PACKAGE --sleep-chain --preview`；保留之前静态睡姿入口。
  右键“入睡/醒来短链（12秒）”或启动`--preview-sleep-chain`播放压缩预览，12秒后回站姿。
  五个资源槽（sleep/awake/yawn/drowsy/sleep）由FramePlan时间表选择；仍使用已批准睡姿摆放。
- 150项行为测试、34项原生自检、consumer仓库检查通过。喂食/拖动/失败/暂停/点击即时抢占；
  reduced原生预览冻结已选sleep静帧；不进入自动动作池。这里是手动短链，不代表真实5分钟空闲/75秒瞌睡已实现。
- App只在临时目录编译/自检，规避工作区fileprovider反复写FinderInfo的问题；严格签名通过，ZIP逐文件核验通过。
  正式1.9二进制摘要不变，没有安装、commit或push。未留下额外常驻桌宠。

剩余：本版过渡视觉确认；完整站立/托腮进入伏桌、醒来回站姿的身体动作；生产睡眠调度与唤醒抢占规则。
不能把压缩12秒预览直接当作自动睡眠链。原始选图及已确认静态原生摆放不需重复审批。


## 2026-09-17 睡姿原生摆放已确认，入睡/醒来关键帧预览 v1

用户反馈“合适，接着做”，因此selected睡姿及sleep-table-native-v1原生大小/摆放已确认，
不再待确认。已确认scale 0.8482811774958408、xFraction 0.0751829509829442、supportEdge 1207/1254。

本轮使用内置imagegen基于选定睡姿制作drowsy、yawn、awake三个候选，用户尚未逐一认可。
睡着源保持b05094ad…不变。完整来源、源摘要、只读差异检查见
Harness `build/sleep-chain-keyframes-v1/sources/`、`qa/source-audit.json`。
用公共Harness v2显式whole-scene互斥图层与hold keyframes串成12秒/5fps/60帧短预览：
睁眼→哈欠→困倦→短闭眼→半醒→伏桌睡着→半醒→睁眼。
`sequence.gif`、160px `contact-sheet.png`为视觉审阅产物；不是生产睡眠时长。
这是四张完整场景的互斥选择，不是身体分层骨架，也没有整场景呼吸/浮动或光流插帧。

验证：公共plan/render/validate通过；全运动60帧逐像素等于选中源在透明底的alpha-over合成，
reduced60帧全部等于首帧awake合成。full仍有已知CONTENT_TOUCHES_EDGE（选定源alpha=1散点），
reduced无警告。已查看160px联系表；未声称动态原生摆放已验收。
**美术稳定门禁未通过**：三张生成帧的下部场景(y>=820)各有约29.7–29.8万RGBA像素变化，
桌子/榻榻米被重绘；形态与色阶可能跳动。技术渲染通过不能当作视觉稳定或生产通过。
qa/verification.json明确production_ready=false。没有把候选接到App或自动睡眠池。

下一步先解决固定环境图层与头部关键帧的一致性，再实现/验证生产链；
保留既有设计要求：真实idle约5分钟后才可入睡，不能直接idle→sleep_table；
瞌睡阶段原设计约75秒，任何工作状态变化/交互应退出；失败/拖动等高优先事件不能等唤醒动画才处理。
暂停/系统睡眠取消，减弱动态冻结且不自动触发；恢复不得补播。以上是待实现规则，非本轮新增测试结果。
完整站立/托腮到伏桌的身体衔接、醒来恢复站姿、独立肢体骨架仍未完成。
正式1.9、consumer原生源码均未改；未新建App、未安装/commit/push，现有未提交修改保留。


## 2026-09-17 选定睡姿已完成原生静态预览，等待摆放反馈

使用用户选定exec-63c4aa0e原图，字节和眼口位置不变；无新绘画、无图像清理。
Harness `build/sleep-table-native-v1/` 包含 Sleep/source.json、base.png、公共plan/render/validate静态hold、
`睡姿预览.zip`、qa/、placement.json、receipt.json、before/与本轮integration.patch。

- consumer增加optional Sleep注册项与preview-only `--sleep PACKAGE`；精确锁定用户选图SHA，正式构建拒绝此参数。
- 右键“睡姿预览（静态60秒）”或preview的`--preview-sleep`入口；60秒后回站姿。
  使用preview身份；喂食、拖动、失败、点击可抢占，暂停/系统睡眠取消；减少动态保留同一静帧。
  这是手动静态摆放预览，不是完整睡眠动作，未加入自动池；base数据不伪造。
- 摆放根据alpha>1/255的可见边界测量：scale 0.8482811774958408、xFraction 0.0751829509829442，
  supportEdge 1207/1254；对齐已认可托腮的可见占地宽度/左边，并以站姿鞋线为支撑。
  只忽略边界测量中的alpha=1散点，不修改原图。尚未获用户原生摆放确认。
- 141项行为测试、33项原生自检、仓库检查通过；160/240/320/400/596可见边界和支撑线检查通过。
  已查看AppKit渲染的160px截图：完整桌子/榻榻米，选定脸和眼口比例保持。
  Harness渲染与选图逐像素一致，0错误；保留ZERO_MOTION（静态hold）和CONTENT_TOUCHES_EDGE
  （原图边缘alpha=1散点）两条警告，不声称零警告。实际alpha>1主体未被裁切。
- 项目目录的fileprovider反复写回FinderInfo，工作区App严格签名不稳定。临时目录的完整字节副本严格签名通过，已打成睡姿预览.zip；验证路径见qa/verified-location.json。工作区展开副本改名preview-bundle-source，避免作为额外App显示。
- 正式1.9安装版二进制摘要复核未变，未启动额外常驻预览，未安装、commit或push。

下一步：用户确认原生大小/支撑线后，为打哈欠→瞌睡→睡着→醒来补齐独立姿态/过渡素材和行为测试。
不要直接把静态睡姿加入自动池，也不要通过整张场景上下浮动假装呼吸；桌子/榻榻米应稳定。
完整分层骨架和睡眠链尚未完成。睡姿静态源在项目build中保存，不把历史被否决pose_prop骨架接回来。


## 2026-09-17 用户选回睡姿首轮微调版

用户附exec-63c4aa0e-666e-493d-b73c-7fa8bb74a33d.png并说“那还是这一版好一点”。
该图已逐字节保存为Harness `build/sleep-table-selected-v1/selected.png`，选择与摘要见selection.json。
此选择覆盖此前“首轮未采纳”的判断；上移眼睛的sleep-table-static-v2不采用。保留选定图的眼口位置。
静态姿态基准已选定，动画/原生摆放仍未验收，正式App未改，无commit/push。


## 2026-09-17 sleep_table 静态候选 v1，等待视觉反馈

用户明确授权进入新的睡姿阶段。内置imagegen以已认可double_cheek/idle_blink/base.png为编辑参考，
制作闭眼伏在桌面双袖上的静态候选，保留深棕发、红白蝴蝶结、圆桌和榻榻米方向。
交付：Harness `build/sleep-table-static-v1/candidate.png`（1254×1254 RGBA，真实透明alpha，边界未裁切），
同目录README.md、inspection.json、preview.html。生成原文件保留，未覆盖既有素材。
已看完整候选图；160/320px HTML预览已制作，但浏览器file URL被安全策略阻止，未完成浏览器小尺寸目检。
当前是完整静态单图，桌子/榻榻米也经生成重绘，不是逐像素锁定，不是分层骨架或动画。
用户尚未认可新睡姿。下一步先收集姿态反馈，再确定生产摆放与动画衔接；不把闭眼hold声称为完整睡眠链。
运行中1.9桌宠和既有资源未动；无commit/push。


## 2026-09-17 旧 App 已按用户要求清理

8个旧预览/中间构建/重复App已移入废纸篓；最近旧版展开回退目录也在压缩逐文件核验后移入废纸篓。
保留正式 `/Users/lyuyuwei/Applications/灵梦桌宠.app`（1.9/build11）与桌面指向它的快捷方式。
回退备份现在为Harness `build/slouch-production-integration/rollback-1.8-build10.zip`；
恢复时解压后将其中 `installed-1.8-build10.backup` 改回 `灵梦桌宠.app`，再按需替换。
清理清单和废纸篓位置见同目录 `cleanup.json`。源码、资源、截图、QA报告和窄补丁未删。
此前README中的candidate/preview/first-build App路径及展开backup路径现为历史证据路径，已不在原处；
依赖这些旧包的对比脚本不能直接重跑，应使用保留回执或从废纸篓恢复对应包。
正式版内容摘要与签名复核通过；未commit/push。


## 2026-09-17 用户确认后已安装 1.9 / build 11

用户回复“是”授权替换。正式路径 `/Users/lyuyuwei/Applications/灵梦桌宠.app` 已更新并启动，
启动回执确认preview=false、Slouch140帧/fallback none，standing140/eating40正常；启动后严格签名通过。
全部文件内容与已验证candidate一致，二进制SHA256为
`271e7de844950599cd6a1b5311e995e362d6b7f07e1f0c3c31ce85e7dacefc22`。
原1.8/build10完整保存在Harness `build/slouch-production-integration/installed-1.8-build10.backup`，
保留原应用身份/偏好设置路径，未改用户偏好。旧独立预览已退出，正式版已启动。
安装首次复制未保留执行权限，已按候选文件权限修复，再完成资源/启动/签名验证；资源字节未改。
证据：同目录 `installation.json`、`qa/installed-assets.json`、`qa/installed-launch.json`。
自动托腮已由确定性行为及原生自检验证；未等待随机挂机现场触发，不声称已完成长期观察。
本条覆盖此前“安装待确认/未替换”状态；没有commit/push。


## 2026-09-17 双手托腮正式接入完成，安装待用户确认

本条优先于下方历史记录。用户已认可静态稿、眨眼和原生大小/摆放，最后反馈“效果可以”；
原生视觉不再待确认。保持 scale 0.86、xFraction 0.07、supportEdge 568/596，未重新生成脸或调整比例。

- 正式源码允许 `build.py --slouch PACKAGE` 在非 preview 模式打包；版本 1.9 / build 11。
- 自动托腮仅在观测到 idle、连续无互动/其他动作至少180秒、素材验证通过、未暂停/减少动态/睡眠、未拖动或打开菜单时参与调度。
  每次30–45秒调度抽样占5%；原吃饭总权重25%不变，所有动作都可选时70%不动。
  托腮持续14秒（两轮7秒），自然结束/被抢占后单动作冷却900秒，动作池休息180秒；冷却只保存在本次进程。
- 喂食、点击、拖动、失败及离开idle会抢占自动托腮。暂停、减少动态及无效资源会取消自动动作；恢复后重新等待，不补播。
  手动预览与自动episode显式区分，原preview专用手动入口保留；正式版采用自动触发。
- 原始静态全场景+睁闭眼局部面板不变。596×596、140帧/20fps，闭眼128–132；未制作独立头部/手臂/袖子动作。
- 验证：131项行为测试、32项原生自检通过；consumer仓库检查通过；Harness full/reduced均0错误/0警告。
  新包与认可预览的PNG/source.json摘要相同；140帧与Harness逐像素相等；160/596px原生截图与认可预览逐像素相等。
  严格codesign通过。原生运行后Finder元数据曾使签名检查失败，仅清理新构建app的扩展元数据后复验通过。
- 可安装产物：`/Users/lyuyuwei/Documents/ChatGPT/Spirite harness/build/slouch-production-integration/灵梦桌宠.app`。
  同目录 README.md、receipt.json、integration.patch、before/、behavior-tests.txt、repository-check.txt、qa/ 为证据与窄回退资料。
- 已安装 `/Users/lyuyuwei/Applications/灵梦桌宠.app` 仍为1.8/build10，未替换；用户要求替换前再次确认。
  下一步仅在用户确认后备份现安装包并替换，验证安装后的签名/资源/启动；本轮没有正式日常运行观察或安装后验收。
- fetch后consumer HEAD与origin/main同为eeb42236b18e534ac8befd5f71561feed6cd5484。
  两仓库原有混合修改保留；本轮未reset/clean/commit/push。不要重跑旧edit.py或应用旧integration.patch。



## 2026-09-17 双手托腮：用户已认可外观/眨眼，原生独立预览接入

用户选定双手托腮圆桌+榻榻米稿，并认可气质调整和Harness眨眼预览；
此次“开始做”后完成原生预览接入，旧单手pose_prop仍是已否决历史素材。

- 新包 assets/reimu/double_cheek/idle_blink：596画布、140帧/20fps、7秒循环，
  128–132闭眼250ms，两个独立PNG由source.json逐帧绑定。
- desktop/macos 新增可选Slouch注册表项、预览专用--slouch构建参数、右键
  “托腮预览（14秒）”与--preview-slouch启动参数；手动动作尊重失败/拖动/喂食优先级。
- 没有加入自主动作池，原25%挂机吃饭概率和随机抽样不变。无托腮包时旧构建保持两素材。
- 已认可摆放：统一缩放0.86、xFraction0.07；以整场景榻榻米底边y568对齐站姿鞋线。
  按膝下y470对齐会裁掉榻榻米，已修正，并加入不裁剪检查。
- 行为108项通过；原生31项通过；素材校验及严格codesign通过；已检查原生160px渲染。
- 独立App：Spirite harness/build/slouch-native-integration/双手托腮预览.app。
  已安装桌宠未替换；完整图层骨架/额外肢体动作未实现，当前为静态场景+眼部面板。
- 历史限制现已解除：用户已确认原生效果；正式接入结果见顶部2026-09-17更新。
- 本轮未commit/push。两仓库已有混合未提交工作保留；窄改动补丁和修改前源码已备份
  在Spirite harness/build/slouch-native-integration/。


## 2026-09-17 用户否决 rework 2 的视觉比例；重做整体方向

用户反馈：“脸的位置大小太过于奇怪了，整个组合都很奇怪”，并指定
`/Users/lyuyuwei/Desktop/灵梦/EatingSetV1-task1单图-已入库副本.png` 为感觉参考。
因此 rework 2 的 READY/GEOMETRY OK/动画逐帧验证只证明技术检查通过，**不能视为美术验收**。
当前 consumer 图层仍是用户否决的 rework 2，不应接入应用或称作完成。

新整体方向稿在 `Spirite harness/build/slouch-rework-3/composition-study.png`；
圆润饱满的脸、大眼、短上身、宽袖与小手，保留托脸动作。此图不是分层动画交付，
未替换 consumer 素材。只放大眼睛的比例试验也未选用。
下一步以用户反馈确认整体方向后重新绘制明确图层，生产继续复用原桌子和榻榻米，
不能从整图分割出图层。原配置、35帧眨眼与支撑边契约保持为验证基线。

## 2026-09-16 slouch rework 2 — palette/head repair, local asset update

Updated only pose_prop/{head,arm_prop,arm_rest,hand_prop,eyes_closed}.png.
Head: built-in ImageGen candidate, uniformly imported at 502/1254 scale and
translated (60,10) on 596x596 RGBA; larger bow and articulated hair highlights.
Arms: user-authorized deterministic chroma correction, original alpha unchanged.
Closed eyes: removed orange socket-cover discs, retained brow/lash strokes.
Eyes_open, mouth, body, table, tatami, configs, z-order and 35-frame blink timing unchanged.

Palette fractions (alpha>=200, max RGB distance<=18): head 10.99%, arm_prop 74.90%,
arm_rest 71.56%, hand_prop 64.86%. support_edge y=547; arm_prop/hand_prop join 830;
160px removed-layer changes arm_prop 137, arm_rest 180, hand_prop 189.
Isolated public Harness 0.8.0 build: 35 frames, no warnings; reduced-motion validates.
Agent inspected 596px/160px side-by-side composites; user visual approval pending.
Build/report/backups: /Users/lyuyuwei/Documents/ChatGPT/Spirite harness/build/slouch-rework-2/.
Original source snapshots preserved there. No app install or runtime publication.
No commit/push: artwork stays local under HARNESS artwork rule; existing mixed
uncommitted changes were preserved. Final live gate outputs are in the QA report.


## 当前接手摘要 · 2026-09-16 第四轮（图层可见性已实现；Harness 已发布 0.8.0，眨眼已跑通）

上一轮发现的「分层构建把 eyes_open 和 eyes_closed 叠在一起画」已修复。
**Harness 核心一行未改**——能力本来就在，缺口全在 consumer 侧。
没有 commit、没有 push、没有 publish。

### 设计：可见性分两条路径

`layer-set.json` 的图层新增 `visibility_group`（eyes_open / eyes_closed 同属 `"eyes"`）；
`animation-set.json` 的 state 新增 `layer_visibility`，声明每组的默认成员与逐帧归属。
`resolve_visibility()` 据此产出两样东西：

1. **恒定可见性 → 直接把图层排除出 source**。整段 state 都不显示的图层根本不进
   `source.layers`，不需要任何 track，**已发布的 0.7.0 就支持**。
2. **随时间变化 → 生成 opacity keyframe track**（`unit: ratio`、`interpolation: hold`、
   `at = 帧号/总帧数`），`value` 0 显示、-1 隐藏（有效系数 `1+value`）。
   只在变化点打关键帧，不逐帧灌。

一个 state 若同时存在同组的两个图层却没声明 `layer_visibility`，**构建直接 fail closed**，
不再静默叠加。这是本轮最重要的行为改变。

### 已验证

- `pose_prop` 现为单帧睁眼姿势，走路径 1，**在已发布的 0.7.0 上构建通过**；
  渲染结果与「仅睁眼」合成**逐像素相同（差 0）**，修复前是与「两层叠加」相同。
- 眨眼变体（35 帧 / 5 fps / 第 32–33 帧闭眼）拿 Harness **工作区**校验与渲染：
  `valid: true`、0 error、0 warning、35 帧 2 条 track；逐帧比对结果
  `................................CC.`，闭眼恰在 32/33，**每帧与预期互斥合成差 0**。
- consumer 97 项测试（新增 9 项覆盖互斥、越界、重复占用、默认成员、未知组、
  作者 track 冲突、仅变化点打帧）、仓库门禁、intake READY、geometry OK、
  eating task_2 无回归（16 帧、`plan_digest sha256:f1571c6a…`）。
- Harness 工作区自身 669 项测试通过。

### Harness 已按维护者授权发布 0.8.0，阻塞解除

已发布的 0.7.0 不接受 keyframe tracks（`MALFORMED_SPEC: unsupported properties: keyframes`），
其曲线只有 `ease_in/ease_in_out/ease_out/hold/linear/sine/triangle`，没有一个能表达离散开关
——连续曲线会让两个眼层同时半透明叠加，正是要解决的问题换种形式。

维护者授权后，Harness 已发布并安装 **0.8.0**（keyframe tracks + 离散 `pulse` 曲线，
669 项测试通过，CLI 与 runtime 均报 0.8.0，从 site-packages 解析）。详见
`Spirite harness/docs/handoff.md` 顶部。Harness 侧尚未 commit/push。

**向后兼容已确认**：eating `task_2` 在 0.8.0 下重建，`plan_digest` 仍为
`sha256:f1571c6a101e34c2…`，与 0.7.0 逐字节一致。

### pose_prop 现为带眨眼的循环

`playback` 35 帧 / 5 fps / loop，`layer_visibility.eyes` 默认 `eyes_open`、
第 32–33 帧 `eyes_closed`。经**公共 CLI** 完整构建：`warnings none`，
`plan_digest sha256:7cdb6701858356b7…`，逐帧 `................................CC.`，
每帧与预期互斥合成**差 0**。

同时把该集合的 `expected_validation_warnings` 收紧为空数组：它是白名单，
pose_prop 现在有真实运动，再出现 `ZERO_MOTION` 就是回归而不是预期。

### 下一步

1. 摆放预览：`ClipPlacement.supportAligned` 已就位，需定 `scale`/`xFraction` 并目视批准。
2. 眨眼节奏（5 fps / 35 帧 / 第 32–33 帧）**尚未目视批准**，需与已批准的站姿 7 秒节奏对照。
3. 第二切片 `sleep_table`。
4. 低优先：清 `body.png` 的袖子残根。
5. 两个仓库都未 commit/push；Harness 的 17 个改动文件含此前各轮工作，提交前需维护者确认。

## 当前接手摘要 · 2026-09-16 第三轮（slouch pose_prop 美术已验收，未提交未发布）

Codex 交付 8 张 → 返工 3 张 → **两个门禁通过、Harness 静态重建通过**。
没有 commit、没有 push、没有 publish、没有改应用。

### 美术状态：pose_prop 可用

- `assets/reimu/layered/slouch/pose_prop/` 8 张齐全；返工只动了
  `arm_prop` / `hand_prop` / `arm_rest`，其余 5 张与首轮逐字节相同，共享层未动。
- intake `READY`（10 图层）、geometry `GEOMETRY OK`（6 项检查全过）。
- 数值证明是真画的而非凑指标：`arm_prop` 638→2606 px 且压在桌面上的接触
  291→**1891** px；`hand_prop` 507→2164 px（eating 单手 1510/2066）；
  `arm_prop↔hand_prop` 连接 67→**830**（下限 600）。bbox 内不透明占比 33–58%，
  填充块会是 90%+。
- **160 px（用户真实尺寸）下姿势成立**：能一眼读出"托脸 + 手肘撑桌"。
- Sprite Harness 0.7.0：`plan → render → validate → preview → contact-sheet → report`
  通过，1 帧，`plan_digest sha256:8c9f7f48…`，warning 仅 `ZERO_MOTION`（单帧符合预期）。

### 本轮修掉的一个泛化遗漏

`DEFAULT_BUILD_DIR` 仍硬编码在 `build/animations/reimu/eating`，导致 **slouch 的构建产物
写进了 eating 的构建目录**。已改为 `default_build_dir(config)` →
`build/animations/<character>/<state_set>`，两个集合再也不会互相覆盖同名 state。
已验证 eating task_2 重建不变（16 帧、`plan_digest sha256:f1571c6a…`、无 warning）。

### 两项已知问题，都不是美术缺陷

1. **分层构建会把 `eyes_open` 与 `eyes_closed` 叠在一起画。** 实测：渲染结果与
   "两层叠加"逐像素相同（差 0），与"仅闭眼"差 3，与"仅睁眼"差 253。
   layer-set 写了 `motion_policy: blink_visibility`，但 builder 没有逐帧图层可见性概念，
   所以单帧静态重建出来是闭眼版。**要做眨眼动画就必须先补可见性语义**
   （或用 `states` 过滤把两个眼层拆到两个 state，需要先定设计）。
   eating 没暴露这个问题，因为生产 task_2 走的是 `exact_frames`。
2. **`body.png` 有 279 px 露在 x190–220 / y379–404**（白色+深描边），是旧袖子残根；
   前臂返工成裸露皮肤后它不再连接任何东西。成因是返工单里"不许动 body.png"的约束。
   真实 160 px 下约 6×5 px，读作袖口边缘，未达阻塞级别。
   另：共享 `table.png` 本身含 202 个强红 + 93 个近白像素散布在整个桌面
   （x123–456, y394–488）——这是 **eating rig 继承来的旧缺陷**，非本次引入。

### 下一步（按依赖顺序）

1. 图层可见性语义——它同时解锁眨眼和整个 slouch 动画，是现在最硬的阻塞。
2. 摆放预览：`ClipPlacement.supportAligned` 已就位，需要定 `scale`/`xFraction`
   两个数字并交维护者目视批准，与 2026-09-07 流程一致。
3. 可选：第三轮清掉 `body.png` 的袖子残根（低优先）。
4. 第二切片 `sleep_table`（伏桌睡着）。
5. 提醒未变：若上线 Codex 生成的美术，应用"关于"文案与 `LICENSE-or-NOTICE.md`
   的"图片由用户提供"必须改。

## 当前接手摘要 · 2026-09-16 第二轮（姿态族前置就绪，等 Codex 交付美术）

用户不会绘画，美术工作交给 Codex，以 `~/Desktop/灵梦/codex-*-task.md` 形式下作业单。
本轮把「Codex 能开工」所需的前置全部做完。**没有画任何美术、没有 commit/push、没有发布。**

### 1. 工具从「只支持 eating」泛化为「支持任意状态集」

- `build_reimu_animations.py`：`load_config` 记录自己被读取的真实路径为 `spec_path`，
  生成的 Animation Plan metadata 与 manifest provenance 不再硬编码 eating 的 spec 字符串；
  新增 `config_spec_path()`（内存中构造的 config 按仓库布局约定回退）与
  `assert_layer_set_binding()`（layer-set 与 animation-set 的 character/state_set 必须一致）。
  顺带堵一个洞：`--config` 指向仓库外时直接 fail-closed，不再把 `../../..` 穿越路径写进产物。
- `check_reimu_layer_assets.py`：新增 `--config`，`layer_set` 路径、
  `base.png` 所在目录、character/state_set 绑定全部从 config 推导，删掉 `LAYER_SET` 常量。
  `validate_runtime_source()` 新增可选 `config` 参数，`scripts/check-repository.sh` 调用点不变。

### 2. 新建 slouch（趴桌/伏案）状态集

- `pets/reimu/layers/slouch/layer-set.json`、`pets/reimu/animations/slouch/animation-set.json`。
- `assets/reimu/layered/slouch/shared/{tatami,table}.png` 是 eating 的**逐字节副本**
  （sha 已核对），所以地面与桌子在两个姿态族之间绝不位移。
- z 序是这个集合必须独立存在的原因：`table` 在 z=60、**压在 body(10) 和 head(20) 之上**，
  桌面上沿 y=379 而直立头部下沿 y=375。因此趴桌的手臂与脸必须在 z>60：
  arm_rest 62、arm_prop 65、head 70、eyes 80/81、mouth 90、hand_prop 95。
- 只声明 `pose_prop` 一个状态。`sleep_table` 是第二切片，未授权前不得声明——
  声明未画的状态会放宽 allowed-PNG 集合、削弱 intake 门禁。

### 3. 新增几何门禁 `tools/check_reimu_pose_geometry.py`

intake 只能证明文件齐全、画布合法。本工具查这个仓库真正返工过的三类缺陷，
约束写在 layer-set 的 `geometry` 块里（数据驱动，不在代码里）：

- `support_edge`：body 的 alpha 最低行必须是 y=547（±2）。已核对 eating 的 body 正好 547。
- `clean_sockets`：head 在 eyes_open 区域内不得有近白不透明像素。
  **拿真实 eating 素材跑，检出 434 个**——正是逼出 `eyes_closed` v1–v5 的那个缺陷。
- `eye_cover`：eyes_closed 必须完整覆盖 eyes_open 足迹（真实 eating 差 4301 px，
  说明现有闭眼层是依赖头部肤色的眼睑补丁，新素材要求更严）。
- `alpha_hygiene`：**区分柔边与散噪**。第一版按「1px 邻域」判，把已批准的 tatami 误判 954 个；
  实测发现那是约 3px 的羽化。改为「离任何实体像素超过 radius/2 的低 alpha 像素」，
  在 isolation_radius=7 时全部已批准素材得分 ≤1，据此把上限定为 8。

### 4. App 侧：摆放规则化，但最终数字仍需目视批准

`ClipSpec` 新增 `supportEdge`，`ClipPlacement` 新增 `.supportAligned(scale:xFraction:)`：
按「把本画布的支撑边对齐站姿鞋线」派生摆放。自检新增一项，证明该规则能在五个尺寸下
复现已批准的 688 坐姿矩形（横向与缩放完全一致，纵向在既有容差内）。
**注意：596 与 688 的合成不成比例**（688 内容底边 582 就是支撑边，596 的榻榻米延伸到 587），
所以不能靠比例换算。现有 688 摆放本身是目视批准的（自检断言只保证误差 <1 参考像素），
因此 slouch 的最终 `scale`/`xFraction` 必须在美术到位后走 Harness 预览 + 维护者确认，
和 2026-09-07 那次一样。本轮没有把第三段 clip 打进应用包。

### 验证

builder+intake 85 项（新增 11 项：第二状态集 7、几何门禁 4）、原生自检 30 项（新增 1）、
行为 99、站姿 5、反应 3、状态契约 28、bridge 14、`scripts/check-repository.sh` 通过。
安装版仍是本日早些时候装好的 1.8/build 10，本轮未重建应用。

### 下一步

- 把 `~/Desktop/灵梦/codex-slouch-pose-family-task.md` 交给 Codex，产出 8 张 PNG。
- 收到后：跑两个门禁 → Harness 静态重建 → 摆放预览交维护者目视批准 → 才谈接进 App。
- 提醒：应用「关于」文案与 `LICENSE-or-NOTICE.md` 现写「图片由用户提供」，
  若上线 Codex 生成的美术，这两处必须改。

## 当前接手摘要 · 2026-09-16（P0 动作系统地基 + P1 pause_chew，源码 1.8/build 10 未安装）

用户要求：先落地动作路线图的 P0（运行时地基）与 P1（零新美术的动作）。
**本轮没有画任何美术**：整个应用仍然只有 11 张 PNG。没有 commit、没有 push、没有安装、
没有替换正在运行的 1.7，也没有注入或模拟任何事件。

### P0 · 动作系统与素材注册表都变成数据

- `PetBehavior.swift`：新增 `ActionSpec`（时长／优先级／字幕／素材／冷却／锁定／反应图／
  帧程序／默认后继）与 `FramePlan`（`still`/`table`/`ramp`/`loop`）。既有六个动作的硬编码
  帧表原样搬进 `FramePlan`，`presentation` 不再按动作名分支。**加一个动作 = 一个 enum case
  + 一行表**。
- 冷却拆两级：`cooldown` 是该动作自己的重复间隔，`globalRest` 是任意两个自主行为之间的
  节奏下限。吃饭两者都是 180 秒，与已批准行为完全一致。
- 加权动作池 `PoolEntry`（含每项的额外资格判定）+ 显式链式后继：池条目可声明 `then`，
  且**只有自然结束**才续接，任何打断都回到 base。`duration: nil` + `maxHold` 的保持型
  动作已支持，供后续趴桌／睡眠链使用。
- `main.swift` 新增 `ClipSpec.registry`：画布边长、帧数、fps、清单身份、Info.plist 摘要键、
  帧文件解析器、窗口摆放位置，每段素材一行。加载器、摆放函数、alpha 命中测试与绘制路径
  全部改读注册表，**加第三段素材 = 一行 + 一个 `PetArtwork` case**。

### P1 · pause_chew（停下咀嚼），零新美术

已批准的挂机吃饭参数逐项不变（60 秒安静、25%、30–45 秒重试、180 秒冷却），
**随机抽样次数与顺序也不变**。25% 被拆成 15% 普通一餐 + 10% 吃完后续接 2 秒咀嚼停顿：
咀嚼放慢两拍（吃饭帧 4-7）→ 半闭眼目光飘移（帧 27，保持 0.6 秒）→ 抬眼（帧 31）→
回中立（帧 0）。**故意不用全闭眼的帧 29**——这是走神，不是眨眼。180 秒冷却从整个
episode 结束时算起，所以停顿不会让她吃得更勤。续接复用已经抽过的那一次 roll，不增加抽样。
右键菜单的"正在进行"判定改为从动作池推导的节点集合，因此新动作不需要再改第二处列表。

### 验证

行为 99 项（原 84 项逐项原样通过）、原生自检 29 项、站姿 5 项、反应 3 项、状态契约 28 项、
bridge 14 项、consumer builder 74 项（跳过 5）、`scripts/check-repository.sh` 通过。
构建产物 1.8/build 10 在 `/private/tmp/.../scratchpad/p0-test.app`（`--preview` 身份，隔离）。
注意：`tools/` 与 `scripts/` 需要带 Pillow 的解释器，用
`/Users/lyuyuwei/Documents/ChatGPT/Spirite harness/.venv/bin/python`，system python3 会假失败。

### 重要发现：P1 的另两项被重新排期，不是"零成本"

App 只加载 `688×688 reference_onigiri_example/eat_blink`（40 帧）和
`1254×1254 neutral_standing_v1/idle_blink`（140 帧）；而分层 rig 与
`eating/task_2` chew-v9（16 帧）都是 `596×596`。**这两条轨道从未接上过。**
所以 `look_at_food` 与坐姿眨眼产出的是 App 从没加载过的 596 素材，需要先做画布对齐
（与站姿↔坐姿过渡是同一件事），不属于纯运行时的廉价收益。

### 下一步

- 决定是否把 1.8 装成唯一应用（按 2026-09-07 的做法先归档 1.7 再替换）。
- P2-6 趴桌姿态族：一次画 3–5 张解锁 5 个动作，需要先定姿态需求清单。
- 596/688 画布对齐，它同时解锁 `look_at_food`、坐姿眨眼和站坐过渡。

## 当前接手摘要 · 2026-09-07（1.7 / build 9 单一合并应用 + 监控探针，优先于全部历史记录）

用户本轮两项要求：「你还是发监控和探针吧」与「我的电脑里有多个灵梦App，我需要留下一个，
将他们的功能合并」。**前一轮「不发探针、不监控」的约束已被用户明确解除，本轮据此执行。**
**电脑上现在只有一个灵梦应用：`/Users/lyuyuwei/Applications/灵梦桌宠.app`，1.7 / build 9。**
安装版 1.3 已被它取代，但完整保留为还原点；没有删除任何文件。
本轮没有新绘图、没有改钩子信任、没有注入模拟事件、没有 commit/push、没有发布、没有派生任务。

### 唯一保留的应用

- `/Users/lyuyuwei/Applications/灵梦桌宠.app`，**1.7 / build 9**，
  bundle ID `local.reimu.onigiri.desktop`，名称 `灵梦桌宠`（不再是预览身份）。
  可执行文件 SHA-256 `8f05abc9efa2ec1d8b4104c501a9f1fd0f16cab0fceaeac78ee1bb5f7be359c6`。
  已启动并在运行；构建、安装后与启动后 `codesign --verify --deep --strict` 均通过。
- 构建记录 `/Users/lyuyuwei/.codex/artifacts/reimu-unified-20260907/灵梦桌宠.app`
  与安装副本**逐字节相同**。`~/Desktop/灵梦/灵梦桌宠.app` 是指向安装路径的符号链接，
  自动跟随本次替换，不是第二个应用。
- 资源与已批准 1.6 预览**逐字节相同**，且是 1.3 资源的严格超集（只多出已批准的
  `Standing/` 眨眼包）。**本轮没有生成任何新美术**，唯一站姿基准摘要复核未变
  （`4b390982469cedbc3b1a0b3792c49a686e2b87b7dda6e5ab12d7bc73cd3e75e7`）。

### 合并的实际内容

1.0 → 1.7 是同一份 `desktop/macos/` 源码的线性演进，**旧包没有 1.7 缺少的功能**。
历史上唯一被移除的行为是 1.3 的「工作中无限吃饭循环／自主咀嚼暂停」，
它此前已由用户批准的站姿默认与有限挂机吃饭取代，本轮未恢复。
所以合并 = 把预览身份承载的 1.6 功能集，用安装身份重建为 1.7，其余包全部归档。
1.7 的功能集：已批准站姿默认与每 7 秒 250 ms 眨眼、紧凑真实状态栏、真实 idle 60 秒后
25% 概率的 8 秒挂机吃饭与 180 秒冷却、右键 4 秒喂食、单击／双击／四连击生气、
拖动与落地、失败优先、暂停、减弱动态、休眠恢复、菜单与指针门禁。行为规则本身未改。

### 归档：17 个历史包，未删除任何东西

`/Users/lyuyuwei/.codex/artifacts/reimu-app-archive-20260907/`：`bundles/` 下 17 个包、
11 个不同可执行文件，按来源目录命名；`manifest.json` 记录原始路径／版本／bundle ID／
可执行文件摘要，全部与移动前一致；`scripts/restore.sh <archived_path>` 可按原路径还原，
不会自动执行。安装版 1.3 还原点为 `bundles/installed-1.3-20260906/灵梦桌宠.app`
（SHA-256 `31c9d9323a6d…`），另有同摘要副本在 `bundles/reimu-anger-20260906_release/`。
偏好域未改写：安装身份沿用它自己的 x=1227 / y=645 / 160 px；预览域原样保留但已无应用。

### 新增的观察能力

角色行为与工作接收器仍然分离。`PetBehavior.onTrace` 是默认 `nil` 的可选记录回调，
记录 base 变化、动作开始／结束（含 `completed`／`preempted_by_*`／`drag`／`left_idle`／
`failed`／`autonomy_off`／`cancelled`）、`meal_attempt`（真实 roll、是否命中、重试间隔）、
门禁与安静计时重置。**随机抽样次数与顺序未改，66 项既有行为检查逐项不变。**
`PetLog` 写 `~/Library/Logs/ReimuPet/behavior.jsonl`，逐行 JSON，1 MiB 上限、一代 `.1`
轮转；`--behavior-log PATH` 改路径，`--no-behavior-log` 关闭，QA 模式不写真实日志。
右键菜单新增真实倒计时一行（非闲置／被抑制／进行中／最早多少秒后尝试，并明示仍是 25%
概率）与「在 Finder 中显示行为日志」。**打开菜单本身是抑制门禁，会重置 60 秒安静计时**，
因此行为日志才是不打扰的观察方式；菜单该行工具提示已写明。

### 监控进程（已启动）

Harness `build/reimu-unified-monitoring-20260907-v1/watch.py`：只读工作快照与桌宠自己的
日志，按变化写 `~/Library/Logs/ReimuPet/watch.jsonl`，持续刷新
`~/Library/Logs/ReimuPet/watch-summary.json`（各状态累计秒数、可触发闲置秒数、挂机尝试
与命中、完成／被打断餐数、手动喂食与点击、门禁计数、首次自动吃饭时间、重启与缺失采样）。
首次观察到真实自动吃饭时发一条本地通知（`--no-notify` 关闭）。
本轮以 12 小时上限、5 秒采样启动，PID 在 `~/Library/Logs/ReimuPet/watch.pid`；
读取 `cat ~/Library/Logs/ReimuPet/watch-summary.json`，
停止 `kill "$(cat ~/Library/Logs/ReimuPet/watch.pid)"`。
交接时刻状态：25 次采样、全程 `working`、可触发闲置 0 秒、挂机尝试 0 次 ——
**因为有真实会话在工作，闲置尚未开始，仍无真实随机挂机结果。**

### 探针结果（全部是真实事件的只读核对）

- **钩子配置**：Codex 10 个、Claude 14 个观察钩子全部在位，无缺失、无外来钩子，
  非 `hooks` 键（`autoMode`）原样保留；钩子信任未改。见 `qa/probe-hooks.json`。
- **真实事件覆盖**：接收器数据库已有 2048 行真实事件。`working`、`round_ended`、
  `interrupted`、`closed` 已由真实事件驱动；**`needs_input` 与 `failed` 从未被真实事件
  驱动过** —— 前者需 `PermissionRequest`／受 matcher 限制的 `Notification`／
  `Elicitation`，后者需 `StopFailure`，这些类型至今 0 行。`PostToolUseFailure` 确实会到达
  （4 次），但 `observer.py` 故意映射为 `working`（工具失败可由代理自行恢复）。
  **本轮没有为了点亮这两个状态而制造任何事件。** 见 `qa/probe-event-coverage.json`。
- **监控与桌宠一致性**：同一批快照由原生 `--status-snapshot`、监控脚本和
  `observer.summarize` 三方评估，**48 次比较零分歧**，含畸形快照、缺失文件和真实快照副本。
  这次探针查出并修好了监控自身的缺陷：合法状态集漏了 `failed`，会把含失败会话的正常快照
  误判为损坏。见 `qa/probe-monitor-agreement.json`。

### 检查与仍未验证

行为 **84**（原 66 项不变 + 18 项记录检查）、原生自检 **29**（原 25 项不变 + 4 项日志检查）、
状态约定 **28**、生气素材 **3**、站姿素材 **5**、Harness **669**（exit 0）、
所选 `cut/` 重新验证零错误零警告、Consumer 仓库检查通过、两仓 `git diff --check` 干净。
证据在 Harness `build/reimu-unified-monitoring-20260907-v1/`（`README.md`、`unified.json`、`qa/`）。

**仍未验证：** 真实随机挂机的日常体感（监控在采集，尚无结果）；`needs_input` 与 `failed`
的真实事件路径；真实任务标题／工具说明／多任务列表／任务跳转；真正的起坐绘画、
悬浮／落地、瞌睡／唤醒。程序化通过不等于视觉批准。两仓大量既有未提交改动全部保留。

### 下一次接手提示

先 `cat ~/Library/Logs/ReimuPet/watch-summary.json` 看监控是否已捕捉到首次真实自动吃饭，
再按用户对 1.7 的反馈微调。没有新反馈时不要重跑已通过的检查、不要重新生成已批准素材、
不要恢复归档包。后续另阶段只选一个方向：真实任务信息接入，或真正起坐／悬浮落地／
瞌睡唤醒的独立绘画与视觉审核。安装替换与发布仍需用户明确要求。

---

## 历史接手摘要 · 2026-09-07（1.6 / build 8 独立预览，已被上方 1.7 单一合并应用取代）

用户在 8142 对齐换图预览后回复「可以，实行后完善交接文档并生成提示词」，
**已确认默认 `cut/` 直接切换、站坐大小／位置及 8 秒挂机吃饭，并授权独立原生接入。**
站姿眨眼 v1 与紧凑真实状态栏此前也已单独确认，不要再次按旧 pending 状态等待。
**本轮实现完成，最终 1.6 / build 8 独立预览已启动；安装版 1.3 保留，未安装替换。**
本轮没有新绘图、接收器／钩子修改、探针、监控、commit/push、发布或派生任务。

### 当前包、素材与阅读入口

- 当前唯一最终候选：
  `/Users/lyuyuwei/.codex/artifacts/reimu-native-idle-meal-20260907-final/灵梦桌宠预览.app`。
  版本 **1.6 / build 8**，bundle ID `local.reimu.onigiri.preview`；沿用独立预览偏好。
  可执行文件 SHA-256：`4d50588b44a4a397d8c107788fc0dc6e35f8405b11fc415bea087cae1955efb4`。
- 同日 `reimu-native-idle-meal-20260907/` 是中间构建，**不是最终包**，已停止进程并保留文件。
  旧 `reimu-native-standing-20260907/` 的 1.5/build 7 也完整保留，由最终候选接替。
- 已安装 `/Users/lyuyuwei/Applications/灵梦桌宠.app` **1.3** 的全部 47 个文件保持原摘要。
  不得将视觉批准或“实行”解释为覆盖安装版的授权，安装仍需用户明确要求。
- Harness：`AGENTS.md` → `HARNESS.md` → `docs/handoff.md`。
  Consumer：`AGENTS.md` → `HANDOFF.md` → `desktop/README.md`，再读
  `docs/desktop-experience.md` 与 `docs/reimu-action-system.md`。
- 唯一站姿：Harness `build/reimu-neutral-20260906/selected-v1/neutral-standing.png`，
  原 1254×1254 RGBA，SHA-256
  `4b390982469cedbc3b1a0b3792c49a686e2b87b7dda6e5ab12d7bc73cd3e75e7`。
  选择记录为 `build/reimu-neutral-20260906/selection.json`，选择的是
  `exec-cb15409b-d9b0-4f49-81e5-79fc95f28591.png`，不是后来全白袜版本。
- 已批准眨眼源：`build/reimu-neutral-idle-blink-20260906-v1/final/` 与 `reduced-final/`；
  三张原眼姿、140 帧／20 fps／7 秒，闭合过程 250 ms。身体／alpha／画布／脚底不变。
- 已批准站坐预览：`build/reimu-idle-meal-transition-20260907-v1/cut/`；`fade/` 未选定，
  `dissolve/` 因双脸重影已否决；不按修改时间选择。
  原网页 8142 是一次性 12 秒示范，不是原生定时循环器。
  收尾检查：8142 返回 HTTP 200；旧 8140／8141 当前未运行，本轮无需恢复，素材仍保留。
- 本轮证据：Harness `build/reimu-native-idle-meal-20260907-v1/`，含 `approval.json`、
  `README.md`、`next-session-prompt.md`、`qa/`。下一次接手提示词已生成在该目录。

### 实际原生行为

- 默认仍为已确认站姿／低频眨眼。只有真实 `idle` 连续安静 60 秒后才首次尝试挂机吃饭；
  每次命中概率 25%，未命中则等随机 30–45 秒再尝试；迟到的时钟只尝试一次，不补播。
- `idle_meal` 单次 8 秒，原 40 帧／4 秒精确两轮；结束直接回原睁眼站姿并续低频眨眼。
  完成或被打断的自动／主动吃饭均阻止下一次自动吃饭至少 180 秒；每次互动及动作结束
  还要求重新安静 60 秒，取两项限制中较晚者。冷却是本进程内单调时钟，不跨退出持久化；
  重启后仍须新的真实闲置 60 秒。手动喂食不受自动冷却限制，重复请求不排队。
- `working`、等待输入、失败、轮次结束、未知、断连均不自动吃饭；`round_ended` 不冒充
  真实闲置。自动吃饭中收到非 idle 状态立即回站姿；真实状态／任务数从不被动作写入。
- 右键喂食保留 4 秒一次；点击可打断自动吃饭，双击、四连击生气、锁定／冷却保持。
  失败立即打断所有反应；拖动立即接管，放下后回最新工作状态。
- 暂停、系统／应用减弱动态、休眠取消自动吃饭；恢复后重新等待，不补播。
  鼠标按住或菜单打开期间不触发自动吃饭，结束后重新等待；素材校验降级也禁用自动吃饭。
- 坐姿与生气图统一沿用已批准的整体等比定位：在 596 参照画布中原 688 方图显示为
  482 方图，Harness bottom_center 偏移 x=2.796511627906966、y=63.26162790697674。
  AppKit 对应 rect=(59.796511627906966, -63.26162790697674, 482, 482)，按窗口宽/596
  等比缩放；命中检测也反算同一个 rect。原 688 图与 1254 站姿按原字节打包，没有重采样源。
- Harness 预览 alpha 支撑边缘 bottom=585；原生使用 AppKit 高质量采样，在 Retina／缩小
  输出中极低 alpha 抗锯齿边缘可有数像素差别，**不称与 Pillow 逐像素一致**。
  鞋底与坐姿裙摆／阴影支撑边缘在视觉上对齐；不是人体脚踝骨架、完整人体分层或绘制起坐。

### 检查、证据边界与下一步

- 本轮 **66 项行为、25 项原生窗口／菜单／计时器、28 项状态约定、3 项生气素材、
  5 项站姿素材**检查通过。挂机边界使用隔离时钟／随机源；不向真实快照注入测试事件。
- Harness 全套 **669 项**通过；所选 `cut/` 重新经公共 CLI/JSON 验证零错误零警告，
  显式 `PYTHONPATH=src`；Consumer 仓库检查及两仓空白检查通过。
  最初系统 Python 缺 Pillow，随后使用既有 Harness `.venv/bin` 重跑仓库检查通过，未安装依赖。
- 最终包构建和启动后 `codesign --verify --deep --strict` 通过。
  Documents 的 `.app` 曾被文件提供程序重加 FinderInfo 而验签失败，因此继续输出到
  `.codex/artifacts`；构建器只清理新输出的 FinderInfo／ResourceFork，不清理来源。
- 制作者查看原生绘制导出的 596／160 px 浅深底对照：`qa/native-comparison-*.png`；
  透明通道、坐姿大小与支撑位置正常。CUA 已打开最终包并看到站姿及真实“工作中 · 2 项”。
  中间构建的右键喂食按钮实际执行后卡片仍为 2 项；CUA 随后选中了状态框窗口，
  因而未捕获这一次真人桌面坐姿全过程，不能冒称已经完整人工验证原生自动挂机。
- 原生自动 8 秒完整生命周期、抢占与恢复已由程序化测试覆盖，**真实闲置随机触发的
  长期体感和最终原生组合尚留用户日常查看**；不安排监控，不重复索要已批准网页视觉。
- Claude 基础连接此前已用真实日志验证；本轮未重复检查。完整审批／失败／重连链路仍
  未全面验证。真实任务标题、工具／文件说明、活动条目列表和跳转仍未实现。
- 下一步先依用户对 1.6 的反馈微调；若无问题，再单独选择一个后续动作或真实任务信息
  接入阶段。真正起坐姿势需另画另审，不一次展开完整动作库，不自动安装。
- 两仓大量既有未提交改动保留。本轮只改 Consumer 行为／窗口／构建版本／行为测试与
  相关文档，以及 Harness 交接和新 build 证据。工作接收器、WorkStatus、StatusBubble、
  源素材和旧安装包保持原摘要；没有声称 GitHub 已同步。

---

## 历史接手摘要 · 2026-09-07（1.5 与待审换图阶段，已被上方 1.6 取代）

用户在 596／160 px 浅深底播放与关键眼姿展示后回复「可以」，**已明确确认站姿眨眼
v1 的眼型与每 7 秒一次、250 ms 的节奏，并授权接入独立原生预览**。
紧凑状态栏也已确认。**默认站姿现已接入 1.5 / build 7 独立预览并启动；未替换安装版。**
原生组合效果仍由用户查看，不把程序检查或网页站姿批准称为新版安装批准。
下方旧记录中的版本、Claude 延期、站姿眨眼 pending 和旧默认吃饭规则均不能覆盖本摘要。

### 本轮最新推进：有限吃饭与换图衔接预览

用户回复「那就往下做」，授权继续下一阶段。本轮已制作并打开
[离线动作预览](http://127.0.0.1:8142/)，目录为 Harness
`build/reimu-idle-meal-transition-20260907-v1/`。**当前候选是 `cut/` 与 `fade/`，
减弱动态为 `reduced/`；仍待用户确认大小、时长与衔接方式，未接入原生挂机调度。**

- 完整片段 12 秒／240 帧／20 fps，只播放一次：站立 2 秒、进入 200 ms、吃饭 8 秒
  （原 40 帧／4 秒循环精确播放两次）、返回 200 ms、恢复站立 1.6 秒并保持。
- 596 px 共用画布。站姿等比缩放 `596/1254`；坐姿等比缩放 `482/688`，位置偏移
  x≈2.797、y≈63.262 px（Harness bottom_center 变换坐标）。全部帧 alpha 支撑边缘
  bottom=585（最低可见 y=584），无整图上下浮动。站姿以鞋底、坐姿以裙摆／阴影
  支撑边缘对齐，**不是已确定共同人体脚踝或脚底的骨架锚点**。
- `cut/` 是对齐后直接切换（页面默认）；`fade/` 是 200 ms 淡出淡入，每帧仅有一个
  完整姿势可见。**两者均为换图方式，没有新绘制的起坐中间姿势，也不是人体分层。**
- 早期 `dissolve/` 虽结构通过，但制作者在第 42 帧看到双脸重影，已否决并从页面选项
  移除，保留为诊断记录；不得把它当选定方案，见 `qa/dissolve-rejected.json`。
- 所有缩放／定位／透明度与帧序均走 Harness 公共 CLI/JSON，显式 `PYTHONPATH=src`；
  本轮无新绘图、无付费 API，原基准与现有吃饭帧不可变。Pillow 只做预览尺寸导出及像素 QA。
- 当前候选 full／hold 均零错误零警告；导出 596／160 px 的动画与静态减弱动态展开后
  共 1440 帧逐像素核对通过，APNG 完整片段仅播放一次。减弱动态的导出是普通静态 PNG，
  不冒称保留了动画帧块。浏览器查看浅／深底、切换中间帧、播放结束保持站立、减弱动态；
  375/414/768/1024/1440 px 页面均无横向溢出，160 px 对照不缩小。

挂机节奏只记录为草案：连续闲置 60 秒后考虑，每 30–45 秒尝试、25% 概率触发，
吃完冷却至少 180 秒。页面不运行调度，不接工作接收器，不显示虚构任务状态／数量。
**下一步先确认本预览，再接独立原生调度**，届时保留右键喂食、失败优先、暂停、
减弱动态、点击冷却、四连击、拖动恢复及动作结束解析最新状态；若用户需要真实起坐动作，
须另用内置 imagegen 绘制并审核完整过渡姿势，不能将本轮淡入淡出冒充该成果。

当前原生预览仍是下述 **1.5/build 7**，安装版 **1.3** 不变。下面原生 37/23/28/3/5 项
检查是上一阶段证据，本轮未修改或重跑原生状态机／接收器；Claude 基础连接不重复验证。
本轮记录、复现命令与保留检查见新目录 README、`qa/`。未安装、commit/push、发布或派生任务。
本轮 Consumer 仓库检查及两仓 `git diff --check` 通过；安装版 1.3 的 47 个文件、
当前原生 1.5 的全部文件、选定基准和 Consumer 运行时代码保持原摘要。


### 阅读入口与当前产物

- Harness：`AGENTS.md` → `HARNESS.md` → `docs/handoff.md`。
- Consumer：`AGENTS.md` → `HANDOFF.md` → `desktop/README.md`，再读
  `docs/desktop-experience.md` 与 `docs/reimu-action-system.md`。
- **当前独立原生预览**：
  `/Users/lyuyuwei/.codex/artifacts/reimu-native-standing-20260907/灵梦桌宠预览.app`，
  **1.5 / build 7**，bundle ID `local.reimu.onigiri.preview`。沿用独立预览偏好，
  与安装版偏好隔离；本轮实际查看 160 px 人物并展开卡片。
- 当前可执行文件 SHA-256：
  `8e6d48caf177eee2ffdb1ab4c540145260ede092023e89d80394fcdcf359a73d`。
- **保留安装版**：`/Users/lyuyuwei/Applications/灵梦桌宠.app`，**1.3**；未覆盖、未退出。
  上一份 `.codex/artifacts/reimu-compact-status-20260907/灵梦桌宠预览.app`
  **1.4.1 / build 6** 完整保留，已被本次站姿预览取代为当前候选。
- 本轮授权、导入、检查与保留证据：Harness
  `build/reimu-native-standing-20260907-v1/` 的 `README.md`、`approval.json`、`qa/`。
  上轮网页重新展示证据在 `build/reimu-standing-review-20260907/`；其 pending 是当时快照。

### 实际运行行为与范围

`PetBehavior.swift` 单独负责角色行为；`WorkStatus.swift`、工作接收器、
`StatusBubble.swift` 和钩子信任均未改。默认外观为站姿：工作中、已观察闲置、轮次结束
使用已确认的低频眨眼；等待、失败、中断、未知或从未观察到事件保持原睁眼站姿。
这些状态的含义和真实计数不因人物站立而改变。普通点击／双击使用站姿眼部帧，
拖动与放下保持站姿静帧；没有新增飞行或落地绘画。

右键喂食仍使用已审核 40 帧、4 秒吃饭素材，一次播放后解析最新状态并回到站姿。
四连击仍显示原已审核坐姿皱眉、红色怒气符号与「むっ！」1.2 秒，点击锁定和冷却保留。
失败优先、暂停、减弱动态、系统休眠恢复和拖动恢复保留；减弱动态保留文字反馈、
保持原站姿。站姿／吃饭／生气各自使用正确 alpha 画布作命中判断。

**工作状态不再驱动无限吃饭循环**，原工作中偶尔暂停咀嚼的调度已随默认站姿移除。
本轮尚未启用自主挂机吃饭；吃饭作为偶尔的有限时长活动仍需下一阶段独立预览。
目前喂食／生气与站姿之间是直接换图，没有声称已绘制起坐过程或完成脚底共用锚点。
不将平面图裁块当人体分层。食物档位公式与 35 动作 JSON 设计登记表未改。

紧凑卡片保留 160/240/320/400 px 人物对应 208/240/280/280 pt 宽、60 pt 高、
28 pt 按钮及展开／收起、边缘定位。**仍只显示真实通用状态和数量；真实任务标题、
工具／文件说明、多任务列表与任务跳转尚未实现。** 网页框体示例文字不是事件接入。

### 唯一美术基准与导入

唯一选定基准：Harness `build/reimu-neutral-20260906/selected-v1/neutral-standing.png`，
1254×1254 RGBA，SHA-256
`4b390982469cedbc3b1a0b3792c49a686e2b87b7dda6e5ab12d7bc73cd3e75e7`。
选择记录 `build/reimu-neutral-20260906/selection.json` 指定
`exec-cb15409b-d9b0-4f49-81e5-79fc95f28591.png`；不是后来的全白长袜稿，勿按修改时间选图。

已确认眨眼来源仍为 `build/reimu-neutral-idle-blink-20260906-v1/` 下
**`final/` 与 `reduced-final/`**，不是旧 `full/`、`reduced/`。
本轮 Consumer `desktop/macos/import_standing.py` 通过显式 `PYTHONPATH=src` 的 Harness
公共 CLI 只读复验两套构建，核对已批准 plan digest 与全部帧摘要，再按文件字节
去重复制成新 Harness build 的 `Standing/`：三张 1254 px 原始 PNG + 140 帧／20 fps 清单。
没有重画、重渲染、重采样或改变 alpha、画布、身体及脚底；打包后再次核对摘要。
原生启动校验清单与 PNG，闭眼文件损坏时明确退到已验证原站姿并在菜单提示，
原站姿丢失则拒绝启动；不会悄悄改用别的立绘。

- [站姿网页预览](http://127.0.0.1:8140/) 保留；其 pending 文案是原构建快照，批准以本摘要
  与新 `approval.json` 为准。未为改状态而覆写旧美术构建。
- [网页状态框示例](http://127.0.0.1:8141/#desktop) 保留，仅供样式参考。
- 上轮两服务 HTTP 200，本轮未重建网页。若 8140 停止，从 Harness 根运行
  `.venv/bin/python -m http.server 8140 --bind 127.0.0.1 --directory build/reimu-neutral-idle-blink-20260906-v1`；
  8141 同理使用 `build/reimu-status-bubble-20260907-v1`。

### 检查结果与证据边界

- Harness full／hold 公共 CLI 验证均零错误、零警告，原帧时序与全部摘要匹配。
- 行为状态机 **37 项**通过；原生窗口／菜单／计时器 **23 项**通过，含四档卡片尺寸、
  27 种屏幕位置、两套图像及 alpha 选择、暂停、减弱动态、拖动位移和恢复。
- 原生状态约定 **28 项**、生气素材 **3 项**、站姿正常／损坏／缺失素材 **5 项**通过。
- CUA 实际查看 160 px 站姿和展开卡片，显示真实「工作中 · 2 项」；实际右键喂食后
  截图确认回到站姿，卡片前后仍为 2 项。没有发送探针或向真实状态注入测试事件。
  原生 self-test 使用隔离 QA 偏好，状态约定测试仅用临时快照。
- 本轮物理拖拽手感未重新人工验证；不能用程序位移检查替代。原生整体搭配仍待用户查看。
- Documents 内开发包曾重新出现 FinderInfo 导致严格签名失败，来源未确定。
  新包按约定构建在上述 `.codex/artifacts` 路径；构建时和 CUA 启动后严格验签通过。
  构建器只清理新输出的 FinderInfo／ResourceFork，不清理源素材元数据。

### 下一步与保留约束

本轮默认待机接入完成，当前独立预览留给用户查看；安装替换仍需用户明确要求。
有限吃饭与换图衔接预览已完成，见顶部本轮推进；确认候选后再接入调度，真实起坐绘画仍未制作；
不一次展开拖拽悬浮、落地、瞌睡和唤醒。真实任务元数据及跳转是独立工程缺口。

Claude 此前延期已解除，基础连接已有真实日志验证。本轮没有重复连接检查、发送探针、
改配置／钩子信任或安排监控；完整审批、错误与重连路径仍未全面验证。
新绘图用内置 imagegen；已授权 Pillow 抠图和眼部补丁，可运行 matte 脚本为
`selected-v1/matte.py`。本轮没有生成任何新美术。

Consumer 编辑前 fetch 成功；两仓大量既有未提交工作保留。未 commit/push、发布素材、
派生任务或调用子代理。Consumer 仓库检查及两仓 `git diff --check` 通过；安装版 47 个
文件、旧 1.4.1 预览、选定基准与原眨眼构建全部文件摘要保持不变，既有工作仅本轮
列出的源码／文档变更。完整清单见本轮 `qa/preservation.json`。

---

以下为保留的历史记录，请按顶部摘要解释其当时状态。

## 2026-09-07 latest: compact status bubble; Claude validation resumed

The user found the native status bar too large and explicitly said Claude can now
connect. This resumes Claude connection validation and supersedes the prior deferral
for that work; no recurring monitor was requested or created.

Compact preview is 1.4.1/build 6 at
`~/.codex/artifacts/reimu-compact-status-20260907/灵梦桌宠预览.app`.
Card width now follows pet size: 160 → 208 pt, 240 → 240 pt, 320/400 → 280 pt
(previously always 360). Card height is 60 instead of 88; button is 28 instead of
36; full height is 96 instead of 136. Fonts are 14/12 pt, with smaller padding.
The same disclosure, placement, clipping/tooltips and state semantics remain.
The previous 1.4 preview is retained but superseded. Installed 1.3 remains untouched.

Claude's 14 observer hooks already exist and the installed receiver matches source.
Read-only inspection of the retained real-event log found one recent main session
with UserPromptSubmit, 16 PreToolUse/PostToolUse pairs and Stop, ending about 17
minutes before inspection. Claude desktop also showed a completed response with
16 commands. The UI local-session identifier does not match the stored hook-session
hash; do not claim a verified ID mapping or infer task-navigation support. No new
Claude task/message, synthetic event or configuration change was needed. This
confirms recent basic lifecycle reception, not every approval/failure/reconnect path.

The native self-test passes 20 checks, including all four compact size mappings
and the existing 27 screen positions. Source art, observer, WorkStatus, PetBehavior
and hook trust are preserved. QA and preservation evidence live in Harness
`build/reimu-compact-status-claude-20260907/`. Fetch succeeded before editing;
no commit/push or publication. Standing blink and idle-meal transition remain separate
pending art/runtime work, as previously recorded.

## 2026-09-07 latest: native status bubble in a separate 1.4 preview app

The user asked to continue. Implemented `desktop/macos/StatusBubble.swift` and
wired it into the native shell: two-line dark capsule, real observed state/count,
unknown-count detail, collapse/expand, persisted disclosure preference, transparent
hit regions and screen-edge positioning. The card is a separate panel following
the character. Collapsing keeps the character and button anchor fixed and does not
restart animation. The old status badge over the character is replaced; reaction
captions remain. No task titles, operation/file descriptions, task navigation or
multi-task list are claimed. The existing observer, WorkStatus, PetBehavior, tier
policy and hook trust are unchanged; no fixture was sent to production.

`build.py --preview` builds a distinct `local.reimu.onigiri.preview` application
with separate preferences and a preview label. Canonical executable artifact:
`~/.codex/artifacts/reimu-native-status-bubble-20260907/灵梦桌宠预览.app` (1.4, build 5).
Both apps inside Harness `build/reimu-native-status-bubble-20260907-v1/` are
superseded development candidates; use its README/QA to resolve the current package.
Installed `~/Applications/灵梦桌宠.app` remains 1.3. Its 47 file hashes and all
approved source/reaction art are unchanged. Current preview uses the reviewed
40-frame eating clip; standing blink and the idle-meal schedule are not imported.

Validation: final native self-test 19 checks, including 27 capsule placements and
real NSButton disclosure actions; 30 behavior, 28 status and 3 reaction-loader
checks pass. CUA confirmed disclosure, live count change 2 → 1, and 160 px selection.
Physical drag feel remains a manual check, distinct from tested native displacement
and geometry. Build signing initially rejected FinderInfo on the new app root;
the builder now removes only FinderInfo/ResourceFork from new outputs before signing.
The Documents package later reacquired FinderInfo alongside FileProvider metadata
and failed strict re-verification; the re-adding actor was not established. The
executable was rebuilt outside Documents in the local artifact directory above.
That current package passed strict verification again after its CUA launch; its
root has only the provenance attribute, and its executable SHA is
`109898c505f3d35ca452e5cc648658164a2f5d15d291482dc05c736f19d47233`.

Read `desktop/README.md`, `docs/desktop-experience.md`, and the Harness build README
and `qa/` records. Fetch succeeded before edits. Existing worktree edits were
preserved; no commit/push or artwork publication. Claude testing remains explicitly
deferred: no inspection, retry or monitoring was initiated. Next review the native
card placement and confirm standing-blink visuals, then integrate the standing base
and preview a bounded idle meal without skipping its seated/standing transition.

## 2026-09-07 latest: current eating/feeding version becomes an idle activity

The user decided: “可以，我打算把灵梦吃饭喂食这一版本做成挂机动作之一”.
Future native behavior uses the selected standing/blinking pose as its default
idle base and reuses the reviewed eating presentation as an occasional idle
activity. Right-click feeding remains a manual entry. A meal finishes by resolving
the latest state; it returns to standing when still idle. Eating is not restricted
to work events, and does not alter or stand in for observed task state.

Read the latest decision at the top of `docs/reimu-action-system.md` and the updated
`docs/desktop-experience.md`. Historical `work_eating`/food-tier restrictions remain
documented as earlier workload/static-atlas design, not gates for future idle meals.
No tier policy or machine-readable registry changed this turn. Existing pause,
reduced-motion, failure priority, drag arbitration and click cooldown remain required.
Episode timing and standing/seated transitions need a future concrete preview;
the original eating clip and reaction art are preserved.

This turn only records the accepted behavior direction. Installed 1.3 still uses
its previous schedule; no runtime/art/hook changes or installation occurred.
Standing-blink approval remains separately pending. Claude remains explicitly
deferred without inspection, retry or monitoring. Fetch succeeded before editing;
no commit/push or publication. Preservation/check evidence is in Harness
`build/reimu-idle-meal-decision-20260907/`.

## 2026-09-07 latest: bubble approved; align the overall Codex pet experience

The user accepted the status-bubble preview: “可以，这个其实我想做的跟Codex的桌宠系统一个样子”.
**Bubble appearance is now approved.** The target includes a floating character,
collapsible activity cards, task status, a future multi-task tray and task navigation.
Read [desktop-experience.md](docs/desktop-experience.md) for the concrete mapping,
current gaps, evidence and staged sequence. Continue the existing standalone macOS
app and Reimu-specific interactions; this feedback does not request a host migration.

Official Pets documentation and the current local bundled atlas contract were
rechecked. Current observer/WorkStatus code still lacks task titles, operation
descriptions and navigable task IDs. Keep preview fixtures isolated; use generic
real status until metadata sourcing is implemented and verified. `round_ended`
does not establish success or unread completion. Card ordering and character
failure priority are separate responsibilities; existing rules stay in place.

This turn records approval and the product direction, with no runtime/art/hook or
installed-app change. The earlier blanket “bubble awaiting confirmation” statements
are superseded; standing-blink art still awaits its separate visual confirmation.
Native 1.3 stays installed. Claude remains deferred, without inspection/retry/monitoring.
Fetch succeeded before these edits; no commit/push or publication. Existing working
files are preserved. Harness `build/reimu-codex-experience-20260907/` holds the
approval/provenance and preservation record.

## 2026-09-07 latest: screenshot-style task bubble preview

The user requested a rounded two-line status bubble matching their screenshot.
Harness `build/reimu-status-bubble-20260907-v1/` contains the standalone preview
at `http://127.0.0.1:8141/#desktop`: dark capsule, bold white title, gray detail,
collapse/expand without moving the character, editable example text and overflow
handling. It reuses unchanged standing-blink exports. Light/dark backgrounds,
160/320 px character sizes and responsive layouts were checked.

**All bubble text is explicitly labeled UI fixture data, not live task progress.**
Read-only inspection of observer.py and WorkStatus.swift confirmed the current
bridge lacks task titles and operation/file descriptions. Native integration and
real metadata sourcing remain future work after visual confirmation; do not infer
file names or inject fixtures into production state. This is not approval of the
standing artwork or authorization to replace installed 1.3. This Consumer edit is
handoff text only; runtime, hooks and installed app remain unchanged. Fetch ran
before editing; no commit/push or publication. Claude remains deferred without
inspection, retry or monitoring. Read the preview README for the exact boundary.

## 2026-09-07 latest: selected standing idle blink preview, not installed

The user requested one independent standing-idle blink preview before native
integration. The sole base is Harness
`build/reimu-neutral-20260906/selected-v1/neutral-standing.png`, SHA-256
`4b390982469cedbc3b1a0b3792c49a686e2b87b7dda6e5ab12d7bc73cd3e75e7`,
from their selected `exec-cb15409b-d9b0-4f49-81e5-79fc95f28591.png`.
The later all-white long-sock draft remains unselected.

Read Harness `build/reimu-neutral-idle-blink-20260906-v1/README.md` and preview
`http://127.0.0.1:8140/`. Current builds are explicitly `final/` and
`reduced-final/`; older directories in that build are superseded, not runtime
sources. Built-in imagegen authored half/closed-eye crops; local Pillow composites
only the two documented eye regions into complete pose alternatives. They are
not anatomical layers. Original source pixels outside the eye regions and the
entire alpha channel remain unchanged. No whole-body bobbing was added.

Harness public CLI plan/render/validate/preview/contact-sheet completed. Full and
reduced modes have zero errors/warnings: 140 frames at 20 fps, a seven-second
loop with one 250 ms blink, 7,745 changed eye pixels, zero changes outside those
regions, fixed canvas/bbox/feet, identical first/last PNGs. APNG and WebP at
596/160 px retain exact alpha and visible pixels; WebP canonicalizes invisible
RGB. Browser review covers light/dark backgrounds, both sizes, pose holds,
playback and manual reduced motion. **Human visual approval remains pending.**

Installed native app stays at the verified 1.3 with the onigiri/annoyed artwork.
This Consumer change is handoff text only. Do not import the standing preview
until the user confirms its visual result. Future integration must retain latest
work-state restoration, pause/reduced motion, failure priority and click cooldown;
keep observation separate from character behavior and never inject fixtures into
production state. Claude validation is explicitly deferred: no checks, retries or
monitoring. Drag/landing and doze/wake remain later stages. Existing working-tree
changes are preserved; the user explicitly forbids commit/push and publication
for this turn. Fetch succeeded before this documentation update.
Final repository checks and both repositories' `git diff --check` passed.
Snapshot comparison confirms every pre-existing workspace file except the two
handoff documents is unchanged, as are all 47 installed application file hashes.
Evidence lives in the preview directory's `qa/workspace-after.json` and
`qa/final-integrity.json`; this is local verification, not remote publication.

## 2026-09-06 latest: approved annoyed artwork installed in 1.3

The user accepted the completed frown/anger-mark/“むっ！” preview. Installed it
at the same `~/Applications/灵梦桌宠.app`, version 1.3. Four rapid clicks now hold
that exact reviewed transparent pose for the existing 1.2-second reaction, then
return to the latest work state. Click lock/cooldown, priorities and work counting
are unchanged. Reduced motion, pause and suspension suppress the pose; failure
clears it. Single/double clicks and feeding retain their existing reviewed frames.

`build.py --annoyed PNG` pins the reviewed SHA and copies it separately to
Resources/Reactions/annoyed.png. Runtime validates its hash, dimensions and alpha;
missing/corrupt reaction art is explicitly reported in the menu and degrades to
text feedback without disabling the original 40-frame clip. No character art
was added to this repository, and no hook/trust/Claude configuration changed.

Validation: 30 behavior checks, 28 work-status checks, 13 native checks and
3 reaction asset-loader cases pass. Actual CUA four-click input displayed the
approved frown, red symbol, Japanese text and “让我吃完嘛”, then returned to
the real “工作中 · 2 项” base. This does not resume or certify Claude validation.
QA and installation record: Harness `build/reimu-anger-install-20260906/`.
1.2 backup: `~/.codex/artifacts/reimu-anger-20260906/previous/灵梦桌宠.app`.
Executable SHA: `31c9d9323a6d0ae8c00d42335503569b2f79775cd86718f0236a79cca1a64011`.
Reviewed reaction SHA: `314f34dcb6d5dbba04555f5996ec3f612e0dc65e7f0c080a027eee1093ccbd3f`.
Local work remains uncommitted/unpushed with unrelated edits preserved. Full
35-action art, sleep/flight and six-tier visuals remain future work; Claude is deferred.

## 2026-09-06 latest: poke reaction artwork under review

**Follow-up: the user approved the expression/local patch direction and requested
a red manga anger mark plus Japanese anger text.** Harness now retains
`angry-final.png` (688x688 RGBA), `frown-patch.png`, and `anger-overlay.png` in the
same build directory. Built-in image_gen authored the independent mark and
“むっ！” text; local Python chroma extraction removes the painted checkerboard.
Two explicit eyebrow/upper-eye polygons receive the approved facial artwork.
`build_reaction.py` reproduces it; `reaction-qa.json` verifies zero pixel changes
outside the face/effect masks and preserved original alpha for the face frame.
Food, sleeves and cheek-ornament occlusion retain original pixels. Light/dark
composites and 160 px were inspected, and the updated page's hold/background
controls were exercised. The old pending question below is resolved. This is
a standalone artwork preview, not yet an installed native 1.2 reaction asset.

After accepting 1.2, the user authorized continuing. Two built-in image_gen
frown drafts are retained only in Harness `build/reimu-poke-art-20260906/`.
Read its README, prompts and QA; `http://127.0.0.1:8139/` provides large/160 px
comparisons and a tested diagnostic toggle. Neither draft is a runtime asset:
the first has a painted checkerboard, and the second is white-background RGB
with measurable changes outside the intended face area (11.46% of protected
opaque pixels exceed max-channel difference 24 after size normalization).

An asynchronous question requests expression feedback and authorization for a
local Python eyebrow/eye patch; the answer is still pending. No patch has been
composited or installed. After approval, preserve all pixels outside the explicit
face patch and the food/sleeve occlusion of the cheek ornament, then verify real
alpha and pet-size playback before integration. Installed 1.2, its source behavior,
40 reviewed frames, action registry and hooks are unchanged. This remains local,
uncommitted work; no third-party artwork was added to this repository. Claude
validation remains deferred until the user explicitly resumes it.

## 2026-09-06 latest: interaction prototype 1.2 installed locally

The user explicitly deferred Claude validation until they notify us, and authorized
moving to the next interaction stage. Do not inspect/retry Claude tasks or schedule
a usage monitor as part of this stage.

`desktop/macos/PetBehavior.swift` now owns input arbitration and transient timing
independently of work observation and the existing single food-tier policy. Single
click, double click, four rapid clicks, manual feeding, drag/landing transitions and
infrequent working pauses use only the existing reviewed blink/eat/hold frames.
Transient reactions return to the latest base; failure wins, reaction spam is not
queued, dragging takes over, and changes in task count do not restart the animation.
The seated hold is an explicit fallback for drag feedback; it is not authored flight.
Full 35-action art, pointer gaze, character sleep chain and six-tier visuals are not
implemented. No source pixels, action registry, hook config, trust record or Harness
core were changed. Read `desktop/README.md` for controls and exact boundaries.

Installed at the same `~/Applications/灵梦桌宠.app`, version 1.2. The 1.1 application
is preserved at `~/.codex/artifacts/reimu-interaction-20260906/previous/灵梦桌宠.app`.
The desktop shortcut, user size/location preferences and live default event source
remain in use. This is still local/uncommitted, not a GitHub publication; unrelated
working-tree changes remain intact.

Validation: 26 deterministic interaction checks, 28 work-status contract checks,
12 native window/timer/menu checks, and the pinned 40-frame/4-second asset load pass.
Actual UI confirmed “嗯？” (single click), “戳到啦” (double), “让我吃完嘛” (four),
“再吃一口” (feeding), and return to the observed work base. Physical CUA dragging
returned `AXError.notImplemented`; physical pointer experience remains a manual
check, distinct from the tested native geometry and drag FSM. QA/installation record:
Harness `build/reimu-interaction-20260906/`. Repository gate and whitespace checks pass.

Next: review this interaction prototype's feel, then author and review proper
reaction/flight/sleep poses before activating those visual actions. Claude live
validation stays deferred until the user resumes it.


## 2026-09-06 local update: independent work observer 1.1

### Latest verification: current desktop task now connected

After the user reloaded Codex and sent “继续验证”, this exact task produced real
SessionStart, UserPromptSubmit, PreToolUse and PostToolUse events. Its hashed
`CODEX_THREAD_ID` matches the receiver session. The production snapshot reports
working with one observed task, and the actual native UI displays “工作中 · 1 项”.
No fixtures were injected and no runtime code/configuration changed. The earlier
missing-events issue for this task is resolved after reload; this does not establish
a complete census of all possible app tasks. This turn's Stop cannot be observed
before the response ends; CLI and another desktop task already supplied real Stop
evidence. Report: Harness `build/reimu-work-observer-20260906/qa/codex-current-task-live.json`.
Claude Desktop Code was checked again: organization usage credits are still
exhausted and Send is disabled. Live Claude verification remains the only pending
provider connection test. Continue with a minimal local Code task when available;
no additional Codex restart is needed for the now-connected task.


### Follow-up verification: desktop events confirmed, coverage still partial

A real **Codex desktop** session was identified by hashing a task ID returned by
`list_threads` and matching it to the receiver's session hash. Its 25 events comprise
SessionStart, UserPromptSubmit, 11 PreToolUse, 11 PostToolUse and Stop. Replaying
those captured records through the native state loader passes all 25 state checks
(idle → working → round_ended). This replay is not a claim of live GUI observation
of that particular desktop task. Evidence: Harness
`build/reimu-work-observer-20260906/qa/codex-desktop-live.json`.

At the preceding check, this older task had **zero received events**, despite being active in the
application task list. The receiver therefore does not cover every already-open
session. A cached session configuration is a hypothesis, not a verified cause;
the reload diagnostic has now succeeded as recorded above. Do not inject a synthetic event into the production snapshot to conceal
that gap. CUA prohibits controlling Codex UI; the user must perform any app restart.
Claude Desktop Code was rechecked and still reports no organization usage credits,
with Send disabled. Its live validation remains pending. No runtime code or hook
trust changed in this follow-up; the original source/tests remain valid.


The maintainer approved implementing the first passive work-event slice using the
separately approved onigiri example. Sources now live in `desktop/`: stdlib Python
hook receiver/installer/tests and the native macOS AppKit shell. Read
[desktop/README.md](desktop/README.md) for installation, semantics, privacy,
verification and rollback. No third-party pixels were copied into this repository;
Harness core and the production Eating Set remain unchanged by this work.

- Installed at `~/Applications/灵梦桌宠.app` (1.1), preserving the 1.0 application in
  `~/.codex/artifacts/reimu-work-observer-20260906/previous/`. The desktop shortcut
  still points to the installed application. It is running against the real default
  snapshot, with no fixture-path override. The native Codex pet package is retained.
- User-level Codex and Claude hooks were merged with backups under
  `~/Library/Application Support/ReimuCompanion/backups/`. Original pre-install
  backup: `1788703038241373000`; final receiver update: `1788703521320890000`.
  Observer SHA-256: `4a13cc0dc6219349884239320ff5d5592a7ef8f3ad41d33e776b4f9a2f1ad0ed`.
  User explicitly confirmed trusting the new Codex hooks through `/hooks`.
  No trust bypass, approval changes, transcript parsing or app internals were used.
- **Real integration verified: Codex CLI 0.153.4.** A minimal read-only, ephemeral
  run returned the expected marker and exit 0. Receiver observed SessionStart,
  UserPromptSubmit, Stop and SessionEnd; snapshot traversed idle → working →
  round_ended. Actual native accessibility state showed working with one task,
  then idle after the 30-second ending display elapsed. The follow-up above separately verifies one desktop session, not all desktop
  tasks or every permission/error event in production.
- **Claude Desktop Code live validation remains pending.** Installed bundled Code
  is 2.1.260. The user clarified they use Desktop Code; CUA confirmed its Code UI,
  but the current UI reports the organization is out of usage credits and disables
  Send. The standalone CLI's unauthenticated status is not a desktop-auth verdict.
  Do not rerun or modify existing user tasks to manufacture validation.
- Repository gate: `./scripts/check-repository.sh` passes using the Harness venv;
  `git diff --check` passes in both repositories.
- Fixture evidence: 14 receiver/installer tests and 28 Python/Swift state-contract
  checks pass. Native window/timer/menu self-test has 12 checks. Actual isolated
  native UI showed working, needs_input, round_ended and interrupted from injected
  fixtures. Fixture files are separate from the live receiver state directory.
- Semantics: observed main sessions only, children excluded, ten-minute silence
  on working/waiting means unknown, Stop means a round ended rather than success.
  Current artwork stays the existing two-action example; the 35-action FSM and
  six-tier visual integration remain next work. The observer reports uncapped
  count only; `app/task-state-mapping.js` remains the sole food-tier policy.
- This is a local, uncommitted addition among pre-existing working-tree changes;
  not a GitHub publication. No existing unrelated work was reset or cleaned.
  Detailed local QA is in Harness `build/reimu-work-observer-20260906/qa/`.

Next: once Claude Desktop Code can send again, validate a new minimal local Code
session and confirm real prompt/stop events. The previously missing older Codex task is now connected after reload. Then implement the interaction FSM using
existing reviewed motions, preserving unknown coverage and the single tier policy.


Last updated: **2026-09-05**

This is the canonical handoff entry for Gensokyo Codex Pets. Every GPT or human contributor should read this file and `AGENTS.md` before changing the repository, then update this file in the same commit as their work.

本文档是 Gensokyo Codex Pets 的固定交接入口。每一位 GPT 或人类维护者在修改仓库前都应先阅读本文档和 `AGENTS.md`，并在同一个提交中同步更新本文档。

## 1. Repository synchronization

- Remote: `https://github.com/lyw-ops/gensokyo-codex-pets.git`
- Primary branch: `main`
- Synchronization policy: repository updates must be committed and pushed to GitHub before the task is reported complete, unless the maintainer explicitly says not to push.
- Safety policy: pull/fetch before assuming remote state; never force-push; never discard another contributor's work.
- Source of truth: the latest successfully pushed commit on GitHub. Verify it with `git status`, `git log -1`, and `git ls-remote origin` rather than storing a self-invalidating commit hash in this document.

If a push cannot be completed, do not claim the handoff is synchronized. Record the blocker, local branch, unpushed commit, validation result, and exact next command in Section 8.

## 2. Read order for a new GPT

1. `AGENTS.md` — binding repository scope and safety rules.
2. `HANDOFF.md` — current state, decisions, and next actions.
3. `README.md` — project overview.
4. `docs/roadmap.md` — milestone sequence.
5. `docs/codex-pet-format.md` — current compatibility evidence.
6. `docs/reimu-design.md` and `pets/reimu/design/visual-spec.md` — Phase 1 design constraints.
7. `docs/reimu-action-system.md` and `pets/reimu/metadata/actions.json` — behavior system, FSM, and action catalog.
8. `docs/workload-food-system.md` — future workload abstraction and current limitations.

Recommended startup checks:

```bash
git status --short --branch
git remote -v
git fetch origin
git log --oneline --decorate -5
./scripts/check-repository.sh
```

### Maintainer-confirmed project priority (2026-09-04)

The primary product is a reusable layered desktop-pet system, not a set of
standalone GIFs and not only a Codex atlas. The intended path is `task source →
clamp active task count to ReimuFoodTier 0–5 → select the eating state → load
and validate its data-driven manifest/layers → compose and play → use the
approved flattened still as an explicit fallback when animation assets are
missing or invalid`. Task sources, tier mapping and playback belong in this
consumer; provider-neutral validation, composition, previews and exports
belong in Sprite Harness. Neither side should duplicate the other.

The eating `task_2` state is the first required vertical slice. Codex standard
rows such as `idle`, `running` and `review` are a separate state space: they
remain useful reviewed assets, but they are not evidence that `task_2` or live
task-count behavior is complete. Until this vertical slice is reconciled and
validated, producing another Codex atlas row is secondary work.

## 3. Current project state

- Project phase: **Phase 1 — Hakurei Reimu only**.
- Current milestone: **`chew-v9-asymmetric-cheeks` is the published and validated `task_2` production loop**. The maintainer approved its art and timing, authorized legacy cleanup/publication, and the Consumer completed guarded import, three no-publish preflights, transactional publication, full repository checks and live task-count-2 loading. V7 and v8 remain preserved legacy/comparison sources. The separate Codex v2 atlas has four approved rows but remains an auxiliary, incomplete compatibility track. No full atlas, `pet.json`, installation, live workload adapter, or task-count-driven Codex behavior exists.
- Repository content: documentation, design constraints, behavior/action specification, metadata example, validation script, approved Eating Set v1 reference art, five runtime identity holds plus the published 16-frame task_2 v9 loop, the layered eating contract/tooling, the frames[] preview app, pinned `task_2-chew-v7/` and `task_2-chew-v9/` exact sources, an explicit task_2 legacy manifest, and reviewed Codex v2 row sources at `pets/reimu/sprites/codex-v2/rows/{idle,waiting,running,review}/`. Guarded importers, builders and regression tests live under `tools/`; generated Harness QA remains ignored under `build/`.
- Animation pipeline status: **production pipeline live and hardened** against Sprite Harness 0.7.0 via its public CLI/JSON contract only. The eating builder now supports `flattened`, `layered`, and fail-closed `exact_frames` inputs. Exact mode pins semantic binding, base/frame SHA-256, numbering, durations, file set and loop endpoints, validates external pixels through Harness, and shares the existing transactional runtime publication path. No Harness core change or private import was needed.
- Sprite status: published `task_2` v9 contains sixteen exact 596×596 frames at 10 fps. The image-right near cheek carries the primary −2/+5px spatially tapered motion while the image-left far cheek responds at only +1/−2px. No whole-face scale, open mouth, blink or central-face movement is used. The loop has six unique RGBA poses, exact neutral endpoints, zero protected-region overlap and zero new colors; runtime frames match the pinned Consumer source byte-for-byte. V7 remains the legacy exact source and the separate Codex `running` row input; v8 remains comparison material only. `idle`, `task_1`, and `task_3` through `task_5` remain one-frame identity holds. Eleven current layer PNGs pass file intake but their static reconstruction differs from the approved neutral by 204,953 visible RGBA pixels, so they are not used as task_2 color truth. Four Codex v2 rows remain separately reviewed; the complete 8×11 atlas lacks seven rows.
- Runtime status: the original Eating Set preview still uses a manual debug task count. The independent `desktop/` hook observer is installed locally; see the dated 1.1 section above for CLI evidence and desktop-source gaps.
- Installation status: no complete original Eating Set Codex atlas package exists. The separate local onigiri example has an installed independent app and a previously installed simplified native Codex pet.
- GitHub status: `main` is the synchronized project branch; verify the latest commit against `origin/main` at the start and end of every task.

## 4. Completed work

- Connected the local repository to the requested GitHub remote on `main`.
- Verified the newly created remote and fetched its state without force or destructive commands.
- Created the project scaffold, fan-work notice, repository instructions, and roadmap.
- Replaced the obsolete four-range workload concept with the discrete `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5` design.
- Specified exact task-count mapping for tiers `0` through `4`, the `5+` visual cap, six meal-density composition plates, and count-preserving fallback semantics.
- Reviewed six maintainer-provided GPT visual prototypes and recorded their provenance, permitted internal use, excluded elements, and high-level composition lessons without committing the images.
- Documented a provisional face, proportion, palette, silhouette, and pixel-production specification.
- Researched the current Codex pet format using public OpenAI documentation, the OpenAI-bundled `hatch-pet` contract, and read-only inspection of the installed desktop app.
- Added a non-installable v2 manifest example and a repository validation script.
- Added this persistent GPT handoff and GitHub synchronization protocol.
- Surveyed nine open desktop-pet/Shimeji projects for behavior architecture (priority ladders, state classes, transition locks, autonomous schedulers, sleep chains, click escalation, drag handling) and recorded the adopted patterns.
- Audited Reimu's first-party characterization against original official texts (game omake/manuals, PMiSS, ZUN print works), separating canon, inferred, and fanon traits.
- Authored the Reimu action system: a two-axis `WorkloadState × CharacterBehavior` model, a priority-banded FSM with base/transient/transition/held state classes, an autonomous scheduler with cooldowns, a sleep chain, interaction reactions, drag-as-flight, a design-only incident chain, a reusable eating vocabulary, and the locked tier 0–5 emotion progression.
- Registered all 35 actions in `pets/reimu/metadata/actions.json`, explicitly marked as a project-internal behavior specification rather than a Codex manifest.
- Extended `docs/reimu-design.md` (standard Codex actions vs. extended behavior vocabulary) and `pets/reimu/design/visual-spec.md` (per-action-category silhouette, expression, prop, and consistency constraints).
- Integrated Sprite Harness as the animation production and validation tool: consumer animation spec, deterministic build entry point (`plan → render → validate --write-qa → preview → contact-sheet → report`, all via the public CLI in `--json` mode with exit-code checks), staged fail-safe publication of `animation.json` + validated frames per state, strict runtime-manifest loading with explicit static fallback, frames[] playback with reduced-motion support in the preview app, extended repository checks (manifest/frame/digest integrity), a 14-test pipeline suite, and the integration contract document.
- Measured and documented the flattened-sprite motion limitation (whole-sprite translation moves the tatami ground line by the full amplitude) and shipped the identity baseline instead of fake motion.
- Fixed dual-mode runtime source validation and unconditional protection of the declared layer root, with regression checks for source-byte immutability. Delivered `docs/task-2-layer-asset-intake.md` and the read-only intake tool; inventoried available art and selected a single full-canvas export policy. No authored art, motion or runtime changes were fabricated.
- Approved and integrated `chew-v7-mother-locked` as the first Codex v2 atlas row source. Added six pinned 192×208 `running` cells, exact provenance/source hashes, a guarded importer, a Harness-only row build (`validate` + M5 `export` + `validate-export`), deterministic rebuild tests, and repository checks that reject undeclared row files or premature installable artifacts.
- Approved and integrated `idle-v1-mother-locked-hair-settle` as the second Codex v2 atlas row source. Added six pinned 192×208 `idle` cells with the shipped row-0 timing, exact provenance/source hashes, a fail-closed importer, an independent Harness/M5 row build, deterministic tests, and the same undeclared-file/full-atlas gates. The row keeps the seated pose and open eyes fixed; only the image-left loose hair curl contour settles 1–2px.
- Approved and integrated `waiting-v1-mother-locked-attentive-brow` as the third Codex v2 atlas row source. Added six pinned 192×208 `waiting` cells with the shipped row-6 timing, exact provenance/source hashes, a fail-closed importer, an independent Harness/M5 row build, deterministic tests, and the same undeclared-file/full-atlas gates. The pose and open eyes remain fixed; only the image-right eyebrow and immediate antialias/skin band rise 1–3px and return.
- Approved and integrated `review-v1-mother-locked-focused-brow` as the fourth Codex v2 atlas row source. Added six pinned 192×208 `review` cells with the shipped row-8 timing, exact provenance/source hashes, a fail-closed importer, an independent Harness/M5 row build, deterministic tests, and the same gates. The rejected split-brow prototype was corrected by fully clearing the original brow band before uniformly lowering the complete brow by 1–2px; eye interiors, eyelids and lashes remain fixed.
- Published the confirmed `task_2` chew-v7 loop from its consumer-owned exact-frame source: guarded import pins the approved Harness animation/plan/source/all 16 frame digests; the eating builder's `exact_frames` mode validates the package as external frames without repainting; repeated independent no-publish builds are byte-identical with zero Harness errors/warnings; runtime tests cover tier-2 mapping, valid load, semantic-mismatch fallback and broken-frame fallback. The approved neutral is runtime `base.png`; the preceding fallback is retained as legacy.
- Researched several chibi eating loops as motion reference only and staged `chew-v8-researched` keyframes and a formal 16-frame loop entirely under the Harness build tree. V8 changes two connected lower-face interfaces rather than one small outline fragment, transports only existing neutral pixels, changes 33–34 pixels at its approved peaks after 160px nearest-neighbor reduction versus v7's 10, and passes Harness with zero errors/warnings. Third-party pixels were neither downloaded into nor used by the project.
- Approved and published `chew-v9-asymmetric-cheeks` after the v8 loop exposed a pointed near-cheek/hair wedge. V9 spatially tapers the near contour and adds a smaller far-cheek response; exact peaks retain compress/puff hashes `57bf28a9…` / `5ba18281…`. Added a guarded importer, five regression tests and a separate pinned 16-frame exact source. Three Consumer no-publish builds share the same plan digest and identical non-location artifacts; transactional publication reproduced the pinned frames exactly.

## 5. Decisions currently in force

### Product and art

- Phase 1 contains Reimu only.
- Art must be original fan-made work; do not extract or copy commercial sprites or third-party fan art.
- Do not generate placeholder or final art before the maintainer approves the visual system.
- Reimu must read through black hair, a large red bow, a red-and-white shrine maiden outfit, controlled chibi proportions, and a manually consistent face system.
- Cozy food and low-table humor may be inspired by the atmosphere of Touhou Mystia's Izakaya, but its assets and layouts are not source material.

### Technical

- Local desktop target: Codex pet v2, 1536×2288, 8×11 grid, 192×208 cells, `spriteVersionNumber: 2`.
- The approved chew-v7 loop was also copied into the Codex standard `running` row because that is the app-selected state while a chat is working. That compatibility mapping does not map from exact task count and does not complete the eating `task_2` vertical slice; `task_2` remains the tier-2 state selected by the consumer's separate food-tier system.
- Latest `task_2` art direction overrides the earlier hand-to-mouth/bite pilot for the first approved loop: every frame starts from the approved mother/base image; the rice ball, hands, sleeves, body, hair, neck, collar, table, eyes and mouth remain fixed; eyes stay open; and chewing is shown only by a restrained one-sided jaw/cheek contour change following the existing three-quarter view. Do not scale the whole face, blink, open the mouth, repaint generatively, change global colors, or move central face details. Dynamic arm/food motion remains a future capability, not current approved pixels.
- `source_mode: exact_frames` is the approved consumer path for this loop. It binds a repository-contained source manifest to `base.png`, verifies every digest/file/duration and byte-identical loop endpoints, skips Harness rendering, and still requires Harness external-frame validation before publication. It is allowed only for separately reviewed exact art, not as an escape hatch around layered-source requirements.
- Production activation completed after explicit maintainer authorization on 2026-09-05. Current task_2 `base.png`, frame 0 and frame 15 are byte-identical approved neutral SHA-256 `0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe`; the preceding fallback SHA-256 `d3139f4ecc428235b4bfd3d227be760cb151d7d3da126f78cfa0923b5ec7ee4d` is retained as `base-eating-set-v1-legacy.png`. Never regenerate either from the non-identical layered reconstruction.
- V7 and v8 are preserved legacy/comparison artifacts; never overwrite them silently. `chew-v9-asymmetric-cheeks` is the approved production `task_2` source. The mouth remains closed; the rice-ball core, eyes, brows, mole, hands, clothes, hair mass, neck, collar, table and tatami remain fixed.
- The approved hair-settle v1 loop maps to standard `idle` row 0. Its six frames use the shipped 280/110/110/140/140/320ms timing; frame 0 is the reduced-motion still. Blink, breathing and the earlier tea-sip idea are deferred and must not be claimed as current pixels.
- The approved attentive-brow v1 loop maps to standard `waiting` row 6. Its six frames use the shipped 150/150/150/150/150/260ms timing; frame 0 is the reduced-motion still. The fixed eating pose and open eyes do not move. The earlier chin-in-hand and eye-flick ideas are deferred and must not be claimed as current pixels.
- The approved focused-brow v1 loop maps to standard `review` row 8. Its six frames use the shipped 150/150/150/150/150/280ms timing; frame 0 is the reduced-motion still. The complete image-right eyebrow lowers by 1–2px after its original position is fully cleared, so only one brow line is visible. Task-slip reading and nod are deferred and must not be claimed as current pixels.
- Partial row work is stored as reviewed 192×208 source cells and validated 1536×208 build output. Do not pad the missing seven rows into a fake final atlas; no `pet.json` or `spritesheet.webp` until all required rows are approved and the full 1536×2288 export validates.
- Public web upload is a separate compatibility target currently documented as 1536×1872.
- Keep visual assets, Codex compatibility, and workload observation as separate layers.
- Use `ReimuFoodTier = 0 | 1 | 2 | 3 | 4 | 5`; do not reintroduce named workload ranges.
- With a valid source, map tier as `min(activeTaskCount, 5)`: tiers `0` through `4` are exact and tier `5` means five or more. Preserve the uncapped observed count outside the visual tier.
- A tier selects an overall meal composition; food-item counts do not need to equal active-task counts.
- The six-plate family progresses from tea-only repose at tier `0`, through increasingly rich meals at tiers `1` through `4`, to a table-filling comic banquet at tier `5`.
- Preserve recurring tea and held-onigiri anchors where state semantics permit, while increasing dish variety and occupied tabletop area at each tier.
- The six older GPT prototypes are internal composition evidence only. Do not commit, trace, crop, downscale, palette-sample, or reuse their pixels; do not carry their task signs or room background into the pet asset.
- Exception decided by the maintainer on 2026-09-02: the approved **Eating Set v1** sheet (their own generated concept art) is committed under `docs/reference/reimu/eating_set_v1/` and is the source of the runtime sprites. Reference art is never loaded at runtime; runtime code loads only `assets/reimu/eating/`.
- Runtime sprites are derived mechanically (`tools/split_eating_sheet.py`): alpha-connectivity panel segmentation, nearest-panel assignment of floating effects, bottom-center anchoring on a 596×596 transparent canvas; no repainting, no non-uniform scaling. Regenerate from an updated approved sheet instead of hand-editing `base.png` files.
- The task-count → eating-state mapping lives only in `app/task-state-mapping.js` (`0 → idle`, `1..4 → task_n`, `>= 5 → task_5`, negative/invalid → `idle`); the character model is `Character → StateSet → State → frames[]` (`app/characters.js`) so additional characters and future multi-frame animation extend data, not code.
- Animation production and validation go through Sprite Harness (`https://github.com/lyw-ops/Spirite-harness`, canonical contract `HARNESS.md`) using only its public CLI/JSON interface. Do not vendor or re-implement harness internals, do not add Reimu-specific logic to the harness core, and do not modify the harness from consumer tasks unless a reproducible harness bug is found.
- The task-count → state policy stays solely in `app/task-state-mapping.js`; the animation pipeline, manifests, and player never re-implement `min(taskCount, 5)`.
- Published runtime animation artifacts (`assets/reimu/eating/<state>/animation.json` + `frames/`) are produced only by `tools/build_reimu_animations.py` after harness validation passes; `base.png` is immutable source and doubles as the explicit static fallback. The runtime never reads `build/` (gitignored, disposable).
- The published Eating Set v1 baseline remains an identity hold. Whole-sprite motion on flattened sources is rejected by measurement. New local motion requires either explicit layers that pass static reconstruction or a pinned/approved exact sequence; never approximate layers from a flattened sprite and never treat a non-identical layered reconstruction as color truth.
- Layered Assets v1 contract (2026-09-03): layered sources live in `assets/reimu/layered/eating/` (immutable, never in `build/`). The layer-set declares 12 possible IDs, of which eight are required for the pilot; do not create empty layers to fill slots. Export **full 596×596 transparent RGBA canvases**, with parts in final composition coordinates (`canvas_policy: full_canvas`), replacing the earlier cropped-layer policy. Anchors/positions remain provisional and unchanged until real PNGs are inspected; do not use their historical translations as placement instructions for full-canvas exports. The exact pack, overlap/ownership guidance and calibration sequence are in `docs/task-2-layer-asset-intake.md`. Pilot remains `task_2`; no other-state expansion or atlas work in this task.
- Layered production order remains intake → placement calibration → static no-publish reconstruction → visual approval → motion → animation approval → publish. The current task_2 static reconstruction did not pass the approved mother's pixel/color gate, so its older 8 fps moving-hand/blink experiment is superseded. Current task_2 uses the separately approved exact 16-frame loop; layers remain future structural material.
- Blink/chew under the current harness v2 contract use complementary opacity cross-fades on explicit `eyes_open`/`eyes_closed` (and mouth) layers; if pilot QA at 160 px rejects the cross-fade, escalate as a reproducible harness feature request (discrete variant tracks), not a consumer renderer.
- Build safety invariants (enforced + regression-tested): the disposable build dir must never equal, contain, be contained by, or alias (relative path or symlink, on resolved paths) the source root, publish root, layered asset root, or any source sprite; all six states publish as one logical generation or every changed state rolls back; failed rollbacks leave `.publish-recovery.json` markers that `scripts/check-repository.sh` refuses; the runtime loader rejects manifests whose `character`/`state_set`/`state` do not match the state slot they are loaded for.
- The build pipeline is offline and deterministic; Sprite Harness M4 generation (paid provider calls) is never invoked implicitly and requires explicit maintainer authorization.
- `ReimuFoodTier`/`task_1..task_5` and the Codex v2 atlas rows are different state spaces; do not map food tiers onto Codex standard rows or claim task-count-driven Codex behavior. The future atlas path is documented in `docs/sprite-harness-integration.md` and requires new per-row visual assets.
- Unavailable or invalid activity data selects tier `0` as an explicitly degraded fallback and must not be reported as an observed zero.
- The current custom-pet manifest does not expose active-task, workflow, tool, or subagent counts. Do not claim live workload behavior until a supported and tested interface exists.

### Behavior and action system

- Reimu's behavior is `WorkloadState (ReimuFoodTier) × CharacterBehavior (FSM node)`; task count never selects an individual animation directly.
- The FSM uses priority bands `FAILED > INCIDENT > REACTION > DRAG > REVIEW > WORKING > AUTONOMOUS > SLEEP > IDLE`; transient actions return to the *current base state* (`returnTo: "base"`), never unconditionally to idle; an unknown node falls back to `idle_relaxed` with logging.
- Core temperament contrast: lazy/unhurried at rest, instantly competent when something happens. Pacing principle: **Reimu should feel alive, not busy** — autonomous one-shots have per-action cooldowns and a global 20–45 s floor, and "do nothing" is the most likely scheduler outcome.
- Sleep is a chain (`idle_yawn → doze_nod → sleep_table`, exit only via `wake_up`), entered only at tier 0 after ~5 minutes of inactivity; no "Zzz" text or floating symbols.
- Locomotion is low-altitude flight; drag is `drag_float` (composed floating, never limp dangling) plus `drag_land`.
- The incident chain (`incident_notice → incident_ready → incident_fly`) is **design-only**: no supported urgent-event trigger exists in Codex today and the registry marks it accordingly.
- The tier 0–5 emotion progression is locked and monotonic: 0 unhurried boredom, 1 crying-while-eating (absurd relief, food restrained), 2 residual tears but visibly easier, 3 openly content, 4 clearly happy (one small sweat cue at most, never fatigue), 5 laughing-while-crying banquet ("how is there this much food", not work collapse).
- Eating uses a shared body construction plus a tier-specific table-composition layer and small expression differences; sprite production must not multiply by six tiers.
- `pets/reimu/metadata/actions.json` is a project-internal behavior specification for future tooling; it is not a Codex manifest and must not be presented as one. Codex-mappable actions vs. extended-runtime actions are separated in `docs/reimu-action-system.md` section 9.

## 6. Open decisions requiring maintainer review

- Review and approve the Reimu action system (`docs/reimu-action-system.md`): the FSM priority bands, the 35-action catalog, the sleep chain, interaction reactions, drag-as-flight, the design-only incident chain, and the autonomous pacing values (cooldowns, sleep-entry delay).
- Approve or revise the 96×104 logical grid with 2× nearest-neighbor export.
- Approve Reimu's neutral silhouette and head-to-body ratio.
- Approve the manually controlled face grid and expression set.
- Approve or revise the provisional palette in `pets/reimu/design/visual-spec.md`.
- Approve the low-table footprint, recurring prop anchors, exact dish vocabulary, expression arc, and tier `0` through tier `5` meal-density plates.
- Decide which prototype foods survive simplification at intended pet size, especially the large hot dish used to distinguish tiers `4` and `5`.
- Decide whether left/right movement should use low-altitude flight and whether mirroring is safe.
- Decide how visual references will be reviewed without committing copyrighted images.

## 7. Next actions

Do these in order; do not skip ahead.

1. Produce and review true art for the remaining eating states, beginning with `idle`/task tier 0 or `task_1`; reuse the v9 exact/layered manifest, validation, playback and fallback structure. Continue reporting missing art rather than using placeholders.
2. Preserve every v7/v8 source and review artifact as legacy; never overwrite it silently. If task_2 changes again, repeat the guarded import → duplicate no-publish preflight → explicit approval → transaction publication sequence.
3. Define the shared cross-tier body/prop coordinates and food-increment rules before creating task_1/task_3/task_4/task_5 motion, so the six states remain one coherent character system rather than isolated illustrations.
4. Add a supported workload adapter only when a real provider interface is available; keep `app/task-state-mapping.js` as the sole `0…5` clamp and preserve manual preview input until then.
5. Preserve the four approved Codex rows and their hashes. Resume `failed`, locomotion, waving, jumping and look-row production only as a separate atlas track; never pad missing rows into a fake atlas.

## 8. Current handoff status

- Blocker: task_2 v9 has no current publication blocker. Expansion still lacks reviewed true art for the other five eating states; the complete Codex pet lacks seven atlas rows and the custom-pet contract cannot receive active-task count. The former `frames/frame_000 2.png` duplicate was verified byte-identical to the preserved legacy fallback, recorded in `legacy-assets.json`, and removed from the runtime frame directory with maintainer authorization.
- Validation commands: activate the Harness venv, then `python3 -B -m unittest discover -s tools -p 'test_*.py' -v`, `node --experimental-default-type=module tools/test_app_runtime.mjs`, and `./scripts/check-repository.sh`. The exact no-publish preflight config/build/report are under `Spirite harness/build/reimu-task2-eating-keyframes-20260904/consumer-preflight/`.
- Verified result: three v9 no-publish Consumer builds validate 16 frames at 10fps with **0 errors / 0 warnings**, plan digest `sha256:44a06825…`, and every output frame matches the pinned source. Their 23 non-location artifact files are byte-identical (canonical tree SHA-256 `779c7e03…`). V9 source manifest SHA-256 is `81aa07c5…`; published animation manifest SHA-256 is `607b6760…`. Runtime base/frame 0/frame 15 remain neutral SHA `0251947e…`, and the named legacy fallback remains `d3139f4e…`. All 104 Python tests, app runtime checks and `scripts/check-repository.sh` pass. A fresh local browser load at `?tasks=2` reports `task_2` and `16 validated frame(s), loop` in full-motion mode. Preflight/publication details are recorded in `consumer-preflight/chew-v9-preflight-report.json`.
- Rebuild check: `python3 tools/build_reimu_animations.py` with the same sources and harness version must be a no-op diff (published output is byte-identical).
- Change-specific review: confirm all maintained documentation uses `ReimuFoodTier`, contains none of the removed four-range mapping or literal one-food-item-per-task rule, keeps the six GPT prototype files outside the repository, keeps `actions.json` labeled as a project-internal specification, keeps the incident chain marked design-only, keeps `base.png` byte-identical to its committed state after any rebuild, and keeps `app/task-state-mapping.js` as the only task-count policy.
- Uncommitted or unpushed work: **intentional per maintainer instruction — do not commit or push this task.** The consumer already contained uncommitted layered task_2 PNGs and a modified layer-set before the Codex row integrations; those pixels were preserved and not used as the task_2 color source. The exact source, importer, builder/runtime tests, documentation and four Codex row integrations are also uncommitted. `origin/main` and local HEAD were both `eeb4223` at the last remote check.
- Latest completed artifact change: archived the redundant legacy-base alias, completed a third production-config preflight, transactionally published v9 to `assets/reimu/eating/task_2/`, and verified it through Harness, full tests, repository checks and a live local browser load. Preserved v7/v8 artifacts, full-atlas packaging, installation, Git commit, and Git push remain untouched.

## 9. Required update procedure

For every repository-changing task:

1. Fetch/pull the current remote state and inspect the working tree before editing.
2. Read `AGENTS.md` and this document.
3. Make only the scoped changes and preserve unrelated work.
4. Run proportionate validation, including `./scripts/check-repository.sh`.
5. Update Sections 3–8 of this document so the next GPT sees the real state, decisions, completed work, next actions, blockers, and validation.
6. Review `git diff` and `git status`.
7. Commit the implementation and its handoff update together.
8. Push the active branch to GitHub. Use `main` unless the maintainer has requested a branch/PR workflow.
9. Verify the remote contains the new commit and the local working tree is clean.

Never mark a task complete while material repository changes exist only in a local working tree.

## 10. Handoff log

### 2026-09-05 — chew-v9 published after guarded Consumer preflight

- The maintainer authorized marking the redundant `frames/frame_000 2.png` copy as legacy and continuing with publication. Its SHA matched `base-eating-set-v1-legacy.png` exactly; `legacy-assets.json` now records the canonical preserved file and retired alias, and only the redundant runtime-directory copy was removed.
- Switched task_2 to the pinned `task_2-chew-v9` source, added compress/puff phase events at frames 2/4 and 9/11, and strengthened the repository gate so published runtime provenance and frame digests must match the configured exact source.
- A final production-config no-publish build matched both preceding preflights (canonical non-location tree SHA `779c7e03…`) and Harness validated 0 errors/0 warnings. Transactional publication wrote 16 source-identical frames and animation manifest SHA `607b6760…`; base and legacy hashes remained `0251947e…` and `d3139f4e…`.
- All 104 Python tests, app runtime checks and repository scaffold checks pass. A fresh localhost `tasks=2` page loaded 16 validated looping frames in full-motion mode. No commit or push was performed.

### 2026-09-05 — chew-v9 formal loop staged after keyframe approval

- The maintainer approved the spatially tapered v9 near cheek and smaller far-cheek response. Built a Harness-only 16-frame, 10fps, 1.6-second loop with two neutral → half-compress → exact compress → cross-mid → exact puff → half-puff → neutral beats.
- Frames 2/9 and 4/11 match the approved v9 keyframe SHA-256 values exactly; frames 0/15 are the approved neutral pixel-for-pixel. The loop has six unique poses and a 1,071-pixel dynamic union with bbox `[218,255,353,280]`; protected overlap and new RGBA-value counts are zero.
- Exported full-canvas disposal=0/blend=0 APNG and lossless WebP at 596px, 160px and 4× wide-face review size. Every export decodes against the logical frames; Harness validation is zero errors/warnings. QA SHA is `09a339df…`; 596px APNG/WebP are `ca88e217…`/`ec1ec8d1…`; 160px APNG/WebP are `b33265bf…`/`8987a517…`.
- No consumer source, runtime manifest or production frame was changed. V7 remains published and v8 remains preserved until separate full-loop approval.

### 2026-09-05 — chew-v9 spatial cheek correction staged

- The maintainer clarified that v8's problem was spatial, not missing temporal interpolation: the near-cheek puff began abruptly and formed a pointed pink wedge against the hair. V9 extends that same contour upward and tapers row offsets from 0 through +1/+2/+3/+4/+5 and back to 0.
- Added a smaller image-left far-cheek response (+1px compress / −2px puff) while keeping the image-right near cheek dominant, preserving the three-quarter view rather than symmetrically scaling the face. Only original neutral pixels are transported at integer coordinates.
- Neutral remains SHA `0251947e…`; revised compress/puff are `57bf28a9…` / `5ba18281…`. They change 729/870 pixels at 596px and 62/60 after nearest-neighbor 160px reduction. Eyes/brows, mole, hands, food core, neck/collar, table and tatami have zero overlap; no new RGBA value appears. Harness validation is zero errors/warnings; QA SHA is `3d62acf9…`.
- A new local page provides a direct v8-pointed versus v9-tapered puff comparison and animated wide-face/596px/160px keyframe toggles. No v9 loop or consumer publication was performed; v7 production and v8 review artifacts are preserved.

### 2026-09-05 — chew-v8 formal loop staged after keyframe approval

- The maintainer accepted the researched v8 keyframe direction. Built a Harness-only 16-frame, 10fps, 1.6-second loop with two identical chewing beats: neutral → half-compress → approved compress → cross-pose transition → approved puff → half-puff → neutral. Frames 2/9 and 4/11 match the approved keyframe hashes exactly; frames 0/15 are the approved neutral pixel-for-pixel.
- The dynamic union is one connected 603-pixel lower-face region with exclusive bbox `[285,257,348,280]`. Adjacent rows change by at most 4px through the compress→puff transition. Eyes, brows, mole, food core, hands, neck/collar, table and tatami have zero overlap; every output RGBA value already exists in the approved neutral.
- Exported full-canvas disposal=0/blend=0 APNG and lossless WebP at 596px plus nearest-neighbor 160px and 4× face review versions. Decode verification matches all logical frames; Harness validates with zero errors/warnings. QA SHA is `d9540ab5…`; 596px APNG/WebP are `e398a105…`/`a88c4c37…`; 160px APNG/WebP are `677287dd…`/`6d7c3821…`.
- No consumer asset, exact-frame source, runtime manifest or production frame was changed. V7 remains published until the maintainer separately approves the complete v8 loop.

### 2026-09-05 — chew-v8 researched keyframes staged after v7 amplitude rejection

- The maintainer reported that the published v7 motion was too small and asked for comparison with other chibi eating loops. The motion study found that readable closed-mouth chewing normally uses an opposing compress/puff beat and a stable food-contact anchor; moving a single outer contour in one direction is insufficient.
- Added a Harness-only `chew-v8-researched` review: neutral is the approved base; compress moves the closed-mouth contact up to +1px and near jaw to −2px; puff moves contact to −2px and the image-right jaw to +5px. The asymmetric cross-pose width excursion is about 10px at 596px. No open mouth, whole-face scale, generated colors, eye/brow/mole/hand/food-core/body/hair/neck/collar/table/tatami motion, full v8 loop or consumer publication was introduced.
- Compress changes 427 source-derived pixels (34 after 160px nearest reduction); puff changes 482 (33 at 160px), both in one connected lower-face region with zero protected overlap and zero new RGBA values. Harness validation passes with zero errors/warnings. Neutral SHA is `0251947e…`, compress `26803651…`, puff `01883920…`, QA `7dd1c686…`.
- A local review page shows a 4× face crop plus 596px and 160px keyframe toggles using animated lossless WebP. This is a diagnostic toggle, not final timing. Published v7 base and animation manifest remain SHA `0251947e…` and `2aa4c3b6…` respectively.

### 2026-09-05 — task_2 exact vertical slice activated and published

- The maintainer explicitly authorized replacing the production task_2 fallback. The guarded importer preserved the preceding base byte-exactly as `base-eating-set-v1-legacy.png` (SHA-256 `d3139f4ecc428235b4bfd3d227be760cb151d7d3da126f78cfa0923b5ec7ee4d`) and activated the approved neutral as `base.png` (SHA-256 `0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe`).
- Enabled the pinned `exact_frames` task_2 state, ran two independent production-config no-publish builds, and compared their entire Harness build trees byte-for-byte. Both validated 16 frames at 10 fps with zero errors/warnings and plan digest `sha256:1e4453e1e68098e9d093e1999c463ca00a8adf7bee9d654b02db5eaf307a15b6`.
- Published `assets/reimu/eating/task_2/animation.json` plus all 16 exact frames through the set-level transaction. Runtime frames match the pinned source byte-for-byte; base, frame 0 and frame 15 are identical. Published animation manifest SHA-256 is `2aa4c3b6f4787155802c1d488cfc7bcbeea26c747be783c9a3c7453407f28c28`.
- Verified the live preview at task count 2 and 160 px: full mode reports and plays `16 validated frame(s), loop`; reduced mode holds the approved still. All 99 Python tests, dependency-free app runtime checks, repository checks and `git diff --check` pass. No commit or push was performed.

### 2026-09-05 — task_2 exact vertical slice staged and validated, production activation blocked

- Audited the three competing task_2 sources. Current runtime base SHA is `d3139f4…`; approved mother-locked neutral SHA is `0251947…`; the technically valid layered reconstruction SHA is `9ad1cbb…` and differs from the approved neutral in 204,953 visible RGBA pixels. The layered composite is therefore structural evidence only, not color truth.
- Added `tools/import_reimu_task2_chew_v7.py` and the pinned sixteen-frame source package. The importer accepts only the approved Harness animation, plan, neutral and all frame digests; its optional activation path refuses unknown bases and preserves the old base byte-exactly as legacy.
- Extended `tools/build_reimu_animations.py` with `exact_frames`: repository-contained semantic binding, hashes, durations, contiguous numbering, undeclared-file rejection, neutral endpoints, protected paths, Harness external-frame validation, shared preview/report/manifest/publication flow. No Harness implementation was imported or modified.
- Ran three independent no-publish task_2 builds from a disposable approved-neutral source root, the last after adding exact PNG format/dimension inspection. Their entire Harness build trees are byte-identical; all validate 16 frames at 10 fps with zero errors/warnings. Added mapping/loader/fallback runtime tests and guarded-import regression tests; all 99 Python tests, app runtime checks and repository checks pass.
- Production activation was attempted through the guarded command but the write was denied because general authorization was not explicit enough for replacing `assets/reimu/eating/task_2/base.png`. No workaround was attempted. Production base, animation manifest and frames remain byte-identical to the previous identity hold. Next owner must obtain explicit permission for that exact replacement before running activation/publication.

### 2026-09-04 — project priority and task_2 art direction reconfirmed

- The maintainer reconfirmed that the deliverable is the reusable layered desktop-pet system and its task-count-driven food tiers, not isolated GIFs or completion of the Codex standard atlas alone.
- The `task_2` vertical slice returns to the head of the queue. Its current approved loop is mother/base-locked, eyes-open and fixed-pose: food, hands, clothing, body, hair, neck, collar and table remain unchanged, while only one jaw/cheek contour moves subtly to show chewing.
- The four approved Codex standard rows remain preserved auxiliary assets. Their existence must not be used to claim that eating `task_2`, live workload input, or task-count-driven Codex behavior is complete.
- No runtime asset, production manifest, atlas package, commit or push was performed for this documentation clarification.

### 2026-09-04 — approved review-v1 becomes the fourth Codex v2 row source

- The maintainer identified a double-line artifact in the initial focused eyebrow. The final keyframe fully clears the original brow band using source skin before moving the complete image-right eyebrow uniformly down 2px, so the corrected peak contains one brow line only. The six-frame loop is neutral → 1px lower → 2px lower/hold → 1px return → neutral; eye interiors, eyelids, lashes, food, hands, body, tea, table and tatami remain fixed.
- Added a guarded importer that accepts only Harness animation `reimu_codex_v2_review_v1_focused_brow_loop`, plan digest `sha256:38e04c4b925ea0c6b836f8d7a31688a317c639ac0d1044a0c88abe4e8a66bb09`, the mother-locked source digest and all six corrected frame digests. It converts nearest-neighbor to six bottom-aligned 192×208 cells and records the shipped review timing 150/150/150/150/150/280ms.
- Added the review-row builder and five regression tests. The public Harness workflow validates external exact frames, produces preview/contact-sheet/report, exports a 1536×208 M5 strip, independently validates it, round-trips all six used cells byte-exactly, and proves the last two cells transparent. Two consecutive builds are deterministic.
- Validation: all 87 tests and `scripts/check-repository.sh` pass. Review source manifest SHA-256 `b7e213a48d462957824b84cff697fe216043d03012931033d6023c2aa746c0aa`; review row atlas SHA-256 `f8971c596d069f1656c616d18918eee3f4cf6b1b67d86cf5ff75bd5121df5f19`. Existing idle, waiting and running hashes are unchanged.
- Scope preserved: no `assets/reimu/eating/`, layered PNG, layer-set, production runtime, full atlas, installable package, commit, or push change.

### 2026-09-04 — approved waiting-v1 becomes the third Codex v2 row source

- The maintainer confirmed the neutral/attentive keyframes and authorized continuing through consumer integration. The six-frame loop is neutral → 1px rise → 3px rise/hold → 1px return → neutral. Only the image-right eyebrow and its immediate antialias/skin band move; eye interiors, eyelids, lashes, food, hands, body, tea, table and tatami remain fixed.
- Added a guarded importer that accepts only Harness animation `reimu_codex_v2_waiting_v1_attentive_brow_loop`, plan digest `sha256:845205fbced82661f2a709beba509db3e43cc44c72016459f64dcbb8bbbd98f8`, the mother-locked source digest and all six approved 596px frame digests. It converts nearest-neighbor to six bottom-aligned 192×208 cells and records the shipped waiting timing 150/150/150/150/150/260ms.
- Added the waiting-row builder and five regression tests. The public Harness workflow validates external exact frames, produces preview/contact-sheet/report, exports a 1536×208 M5 strip, independently validates it, round-trips all six used cells byte-exactly, and proves the last two cells transparent. Two consecutive builds are deterministic.
- Validation: all 82 tests and `scripts/check-repository.sh` pass. Waiting source manifest SHA-256 `975296d888b980be1a0e79ec9edc7edee3688b44e000b8d247aee107a9d50c45`; waiting row atlas SHA-256 `d0b2d3fd4670345c96caca636a4c8aaf22d64d580c62236a5e524511e2683431`. Existing idle and running hashes are unchanged.
- Scope preserved: no `assets/reimu/eating/`, layered PNG, layer-set, production runtime, full atlas, installable package, commit, or push change.

### 2026-09-04 — approved idle-v1 becomes the second Codex v2 row source

- The maintainer confirmed the two keyframes and full six-frame loop, then authorized consumer integration. The only motion is the image-left loose hair curl lower contour settling by 1–2px; eyes remain open and the face, food, hands, body, tea, table and tatami stay fixed.
- Added a guarded importer that accepts only Harness animation `reimu_codex_v2_idle_v1_hair_settle_loop`, plan digest `sha256:b0a0df96a302a2282db7ffba9512d6f84d001298ebaaeca78611985cc3732b24`, the mother-locked source digest and all six approved 596px frame digests. It converts nearest-neighbor to six bottom-aligned 192×208 cells and records the shipped idle timing 280/110/110/140/140/320ms.
- Added the idle-row builder and five regression tests. The public Harness workflow validates external exact frames, produces preview/contact-sheet/report, exports a 1536×208 M5 strip, independently validates it, round-trips all six used cells byte-exactly, and proves the last two cells transparent. Two consecutive builds are deterministic.
- Validation: all 77 tests and `scripts/check-repository.sh` pass. Idle source manifest SHA-256 `0de89904a02c6ec8ecb6feb277d3a9d6246fb90e978738a1632e9aeeec91a03c`; idle row atlas SHA-256 `ee60d476addbfe24a0962fb17c7ccea5d3bdd78dcbc9eb873e09dceba86076c4`. Existing running hashes are unchanged.
- Scope preserved: no `assets/reimu/eating/`, layered PNG, layer-set, production runtime, full atlas, installable package, commit, or push change.

### 2026-09-04 — approved chew-v7 becomes the first Codex v2 row source

- Read the current consumer contract and confirmed that food-tier `task_2` cannot be selected by the current custom-pet manifest. The maintainer authorized mapping the approved fixed-pose chewing loop to standard row 7 (`running`), the state Codex selects while a chat is actively working.
- Added a guarded importer that accepts only the confirmed Harness animation id, plan digest, mother-locked source digest and all 16 frame digests. It selects source phases `0,2,4,6,7,7`, performs nearest-neighbor 596→192 sampling, bottom-aligns at `(0,16)` in 192×208, introduces no new visible colors, and writes six pinned source cells plus provenance.
- Added the running-row builder using only the public Sprite Harness 0.7.0 CLI: plan → external exact-frame validation → preview/contact sheet/report → M5 export → validate-export/report. The 1536×208 row strip round-trips all six used cells byte-exactly and verifies the last two cells fully transparent.
- Added five tests covering the checked-in source, digest tamper, dimension tamper, undeclared PNGs, real Harness integration and deterministic repeat build. The older repository-source fixtures now explicitly clear copied working-tree layer PNGs so optional participation is controlled by each fixture. All 72 tests pass. Repository checks now accept exactly this reviewed row source and reject premature `pet.json`/`spritesheet.webp` artifacts.
- Validation: row source manifest SHA-256 `c09f5f1b2aee4e313dbfe56419055dd68b15c02009a70318dfcb46bf7d9a8485`; row atlas SHA-256 `0f26e3de85b71a154c15a760c3703ee33328ef65df9dcfdf097e79483055b8e3`; Harness frame and export validation both 0 errors / 0 warnings; repository scaffold check passed.
- Scope preserved: `assets/reimu/eating/` unchanged; pre-existing uncommitted layered work untouched; no full atlas, installable package, commit, or push.

### 2026-09-03 — final production gates and task_2 intake boundary

- Started from fetched consumer main `6f60fc9` and Harness main `619d4a7`, both clean. Confirmed HARNESS.md and the layered v2 contract; no reproducible Harness bug or Harness edit was needed.
- Repository source validation now branches on `source.mode`. Flattened bindings retain the base.png rule; layered bindings require the official contract and recompute the current state-filtered, z-ordered source IDs. Present optionals must be bound, absent optionals must not be bound. Missing/unknown/duplicate/extra layers, stale SHA-256, unreadable/non-RGBA/incompatible PNGs and wrong layer-set paths fail. State selection and path resolution are shared with the existing builder.
- Builder loads any configured layer-set metadata before destructive work, even when all six requested states are flattened. Equal/inside/containing/symlink-alias layer-root build paths are rejected; tests prove no deletion/build invocation and unchanged source bytes.
- Added `tools/check_reimu_layer_assets.py` and `docs/task-2-layer-asset-intake.md`. Intake is read-only, does not render, calls no provider, and makes no visual-content judgments. PNG inspection uses Pillow; no Harness internals or new rendering backend were introduced.
- Inventoried the source tree and maintainer archive. Two archive PNGs match the committed sheet/single-render SHA-256; the other two PNGs are flattened concept sheets. No authored layers were available. Source images were only read, never cut apart or altered.
- Full 596×596 RGBA canvas policy replaces cropped exports for the pilot. No anchors/positions were guessed or promoted from provisional. The eight-file minimum and recommended eye/food variants are explicit; static reconstruction precedes production motion, and visual approval precedes publication.
- Verification: 67 tests passed, real CLI integration included; repository check and diff check passed. Six-state identity rebuild ran twice with no runtime diff. Intake returned the expected ART ASSET REQUIRED and exact eight missing required paths. Regression fixtures are synthetic and temporary, not final art.
- Result A: **Reimu Layered Assets v1 — production tooling ready — task_2 intake validation ready — ART ASSET REQUIRED**. Real static reconstruction, animation and visual QA are pending. Current runtime remains unchanged. Next owner: maintainer/art author supplies the PNGs in the intake pack.

### 2026-09-03 — pipeline hardening and Layered Assets v1 contract

**Phase A — consumer pipeline hardening (`tools/build_reimu_animations.py`, `app/`, `scripts/`):**

- Added a fail-closed filesystem boundary validator: before any `shutil.rmtree`, the disposable build directory is checked (on fully resolved paths, so `..`, relative aliases, and symlinks are caught) for equality, containment, or reverse containment against the source root, publish root, layered asset root, and every source sprite. Covered by 11 regression tests, including one proving `base.png` bytes survive a malicious `--build-dir` pointing at the source tree.
- Replaced per-state publication with a set-level transaction: stage all states → re-verify the staged package → commit state by state → on any failure roll back every state changed by the run. Six failure-injection tests prove the publish tree ends all-old or all-new, never mixed. A failing rollback writes `.publish-recovery.json`, preserves the staging directory (which still holds the previous generation), and raises an explicit error; `check-repository.sh` fails while a marker exists. `base.png` is never moved, backed up, or replaced by the transaction.
- Hardened the runtime loader: `app/characters.js` declares the state set's semantic binding and `app/animations.js` rejects any manifest whose `character`/`state_set`/`state` do not match the slot (verified in-browser: `task_3`'s manifest at `task_2`'s path falls back explicitly with "manifest state mismatch"). SHA-256 integrity remains a build/`check-repository.sh` gate by design — no crypto in the browser.
- Verified: `check-repository.sh` passes; 43 unit/integration tests pass; a full real rebuild of all six states publishes byte-identically (no git diff in `assets/`); loader re-verified in-browser with all six states `animated`.

**Phase B — Reimu Layered Assets v1 (contract + production system, art pending):**

- Established the layered source tree `assets/reimu/layered/eating/{shared,idle,task_1..task_5}/` (version-controlled authored PNGs only; never in `build/`; empty pending art) and the asset-production specification `docs/reimu-layered-assets-v1.md` (12-layer schema, per-layer includes/excludes/reason, 596×596 reference-canvas coordinate rules, z-order with the table-in-front occlusion, allowed/forbidden transforms — the tatami must never breathe — naming/alpha/provenance rules, pilot QA checklist).
- Added the machine-readable contract `pets/reimu/layers/eating/layer-set.json` (anchors, provisional positions, unique z, shared vs state scope, `{state}` path templating, optional layers); `check-repository.sh` validates its JSON, id/z uniqueness, canvas, and that the layered tree holds only PNGs/docs.
- Upgraded the single builder (no second builder) to two source modes: `flattened` (plan v1, unchanged, byte-identical output) and `layered` (`source_mode: "layered"` consumer key → Animation Plan v2 inline `source` composed from the layer set, `plan` invoked without `--source`, per-layer SHA immutability verification, layered manifest source binding). Missing required layer PNGs fail closed with `ART ASSET REQUIRED`. The runtime manifest format and app player are untouched — the player cannot tell v1 from v2 builds.
- The layered path is integration-tested end to end against the real sprite-harness 0.7.0 CLI using synthetic authored layers with a real local-motion track (4 distinct frames, deterministic rebuild, publish with layered source binding).
- Decision: pilot state is `task_2` (held food + table food + transitional expression; complex enough to exercise body/head/face/hand/prop decomposition, without the tier 5 banquet). Blink/chew use explicit variant layers with complementary opacity cross-fades under the current harness v2 contract; discrete variant tracks would be a future harness feature request if 160 px QA rejects the cross-fade.
- Explicitly NOT done, by policy: no layers derived from the flattened sprites, no placeholder/AI Reimu art, no M4 provider generation, no Codex atlas production (blocked on the non-eating action assets).
- Next owner: obtain maintainer review of the layer contract, then the **ART ASSET REQUIRED** pilot PNGs for `task_2` (exact list in `docs/reimu-layered-assets-v1.md` §Pilot); after committing them, measure real positions into `layer-set.json`, flip `task_2` to `source_mode: "layered"` with restrained pilot tracks, build, and run the QA checklist.

### 2026-09-03 — Sprite Harness integration and identity baseline

- First production use of Sprite Harness (`lyw-ops/Spirite-harness`, 0.7.0) as the animation build/validation tool, strictly through the public `sprite-harness` CLI/JSON contract; no harness core changes and no Reimu-specific harness logic were needed.
- Added the consumer animation spec `pets/reimu/animations/eating/animation-set.json` (shared defaults + per-state overrides, expanded deterministically into one legal Animation Plan per state — no six copy-pasted plans) and the build entry point `tools/build_reimu_animations.py` (`plan → render → validate --write-qa → preview → contact-sheet → report`, exit codes checked, `--json` everywhere, validation failure blocks publication, staged fail-safe publish, source SHA verified unchanged, harness version + plan digest recorded).
- Published per-state runtime artifacts `assets/reimu/eating/<state>/animation.json` + `frames/frame_000.png` for all six states; `base.png` remains immutable and repeated builds are byte-identical.
- Decision: the baseline is an **identity hold** (one validated frame per state). A restrained whole-sprite breathing experiment (±2 px translate_y) validated cleanly but measurement showed the tatami ground line moving by the full amplitude with the table and food — whole-scene bobbing reads worse than a stable still at 160 px. Local eating motion requires explicit layered source assets (Animation Plan v2); recorded in `docs/sprite-harness-integration.md` together with the future Codex-atlas boundary (food tiers are not Codex rows).
- Upgraded the preview app: strict manifest loader (`app/animations.js`), token-guarded single frame player with per-frame durations/loop, reduced-motion support (OS preference + QA toggle), instant state switching without flicker, and explicit logged/visible fallback to `base.png` on missing or malformed manifests. `app/task-state-mapping.js` is untouched.
- Extended `scripts/check-repository.sh` (manifest integrity: contiguous numbering, per-frame digests, reduced-motion frame, source binding, 596×596 RGBA frames) and added `tools/test_build_reimu_animations.py` (14 tests: spec composition, harness discovery errors, manifest determinism, publish rollback, end-to-end + determinism + validation-failure integration tests against the real CLI).
- Verified in-browser: all six states load as `animated`, task-count edge values map correctly, playback cycles frame order exactly and stops on state switch, non-loop states hold the last frame, reduced motion holds the declared still, missing/malformed manifests fall back with explicit status.
- Next owner: get maintainer review of the identity baseline, then produce explicit layered Reimu PNGs and move the eating states to Animation Plan v2 local motion; do not fake layers from the flattened sheet and do not invoke harness M4 generation without explicit authorization.

### 2026-09-02 — Eating Set v1 static prototype

- Inventoried the maintainer's local design archive (`~/Desktop/灵梦`); selected the approved 1254×1254 six-panel transparent sheet (low table + tatami + chin-in-hands idle) as Eating Set v1 and its companion task_1 single render as reference; rejected two superseded concept sheets and five downloaded third-party fan-art files (the latter are barred from the repository by `AGENTS.md`).
- Committed the approved sheet and companion render under `docs/reference/reimu/eating_set_v1/` with provenance notes, per explicit maintainer instruction.
- Wrote `tools/split_eating_sheet.py` (deterministic alpha-connectivity segmentation; panels 5/6 touch at the tatami corners and are separated by an erosion-seeded nearest-seed split; hearts/sweat/steam/sparkles assigned to nearest panel; 596×596 bottom-center-anchored transparent canvases) and generated `assets/reimu/eating/{idle,task_1..task_5}/base.png`.
- Built the static preview app (`app/`): `Character → StateSet → State → frames[]` registry, the single task-count→state policy boundary in `app/task-state-mapping.js`, and a debug task provider (buttons −1/0–6/10, numeric input, keyboard, `?tasks=N`), plus display-size and background QA toggles. No animation, per milestone scope.
- Extended `scripts/check-repository.sh` to require the new files and validate all six sprites as 596×596 RGBA PNGs.
- Next owner: get maintainer review of the six runtime states at pet size, then plan animation frames and the real workload adapter; do not claim live Codex integration.

### 2026-09-02 — Reimu action system and behavior FSM

- Surveyed Ice-teapop/desktop-pet, clawd-buddy, clawd-on-desk, kokoronoka/desktopPet, He2y/desktop_pet, Shimeji-ee/Shimeji-Desktop, Adrianotiger/desktopPet, and vscode-pets for behavior architecture only; adopted patterns are documented with sources in `docs/reimu-action-system.md` section 2.
- Audited Reimu's first-party characterization (game omake/manual texts, PMiSS, IaMP profile, ZUN print works) and recorded a canon/inferred/fanon table; poverty-mania and other flanderizations are explicitly excluded.
- Added `docs/reimu-action-system.md`: two-axis model, priority-banded FSM, base-state return rule, transition locks, autonomous scheduler pacing, sleep chain, interaction set, drag-as-flight, design-only incident chain, locked tier emotion progression, Codex-standard vs. extended action split, and sprite-economy strategy.
- Added `pets/reimu/metadata/actions.json` (35 actions, project-internal specification) and extended `docs/reimu-design.md`, `pets/reimu/design/visual-spec.md`, `docs/references.md`, and `scripts/check-repository.sh` accordingly.
- Next owner: obtain maintainer review of the action system and pacing values, then proceed to the Milestone 1 model sheet; do not begin sprite production or claim extended-runtime support.

### 2026-09-02 — GPT composition-prototype review

- Reviewed the six local GPT-generated images labeled from `0 tasks` through `5 tasks`; the originals remain outside the repository.
- Corrected the earlier literal serving-slot interpretation: task count selects a meal-density composition rather than an equal number of visible food items.
- Recorded the tea-only tier `0`, eating transition at tier `1`, growing meal scale through tier `4`, and comic table-filling tier `5` direction.
- Excluded prototype task signs, full backgrounds, environmental decorations, glossy face treatment, and source pixels from the final pet asset.
- Next owner: approve the simplified prop set and expression arc, then author an original cell-scale model sheet.

### 2026-09-02 — discrete Reimu food-tier correction

- Removed the former four-range workload model from repository instructions and maintained documentation.
- Established exact tiers `0` through `4` plus capped tier `5` for five or more active tasks.
- Defined six stable food composition plates, centralized selection and degraded fallback behavior, and tier-specific future acceptance tests.
- Kept the existing technical limitation explicit: the current static Codex pet manifest cannot receive task counts or select these variants live.
- Next owner: review the six-tier composition system and remaining Milestone 1 visual decisions before producing art.

### 2026-09-02 — Milestone 0 and persistent handoff baseline

- Established the initial repository and Reimu-first documentation scaffold.
- Recorded current Codex v1/v2 findings and the lack of a native custom workload-count hook.
- Added the root handoff document and required GitHub synchronization workflow.
- Next owner: obtain maintainer decisions in Section 6 before creating Reimu art.
