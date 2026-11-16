# 艾伦城市 · Alen City Development

Europa Universalis IV / Anbennar 加韦德城市发展署与任务树模组。

## 当前内容

- 经济界面右上角的“发展署”入口，包含地图、12 座城市及三级发展展示。
- 加韦德第一阶段任务树：5 列、20 个任务，仍在编写中。
- 威利亚姆改革开局事件、灾难与加韦德内战，以及第五列任务事件和奖励前瞻。
- 中文本地化与地图 SVG 制作源文件。

## 安装

依赖 Anbennar: A Fantasy Total Conversion，当前以 EU4 1.37.5 为基线。

将本仓库内容放入 EU4 用户目录下的 `mod/艾伦城市`，通过启动器建立对应的本地模组描述文件并启用。已有本地模组时可将 `path` 指向此仓库的绝对路径。使用中文界面需与当前 Anbennar 汉化及双字节补丁配套。

经济页城市入口已在游戏中检查显示及关闭。新版任务树接入了用户提供的 8 个奖励修正，奖励数值及持续时间保留原稿设置。修正处有中文注释，原稿保存在制作源文件中；详见任务修正说明。任务事件条件 frozenmaw_53_happened 尚待配套事件设置，未擅自取消。任务树尚未实机验证。

改革内容只做静态验证，未启动游戏。固定 12k 贵族叛军与尚未设计的阿德肖叛乱按用户要求暂留接口。完成“国王的左膀右臂”立即解除本灾难施加的富商贷款禁令；三个特殊机制在灾难结束后停用。事件、期限与兼容边界见 [改革制作说明](制作源文件/威利亚姆改革_制作说明.md)。

## 制作与兼容

`制作源文件` 保存中文本地化原文、地图源文件、任务原稿和检查清单。游戏用本地化包含双字节转义，编辑时请修改中文原文并重新转码。

运行 `python "制作源文件/重新生成整包.py"` 可重建经济 GUI 及城市、任务、改革三份本地化。中文原文也可通过 `EU4本地化转码.py` 单独转换。

脚本 `.txt/.gui/.gfx` 使用无 BOM 编码，本地化 `.yml` 保留 UTF-8 BOM。可运行 `python tools/check_encoding.py` 检查；打包脚本也会执行同一检查，防止任务列因编码而被误读成单个任务。

`missions/Gawedi_Missions.txt` 保留用户提供的原名和内容，用于禁用 Anbennar 原版加韦德任务。自定义第一阶段任务独立放在 `missions/a13_stage1_missions.txt`。

本模组覆盖 `interface/countryeconomyview.gui`、`missions/Gawedi_Missions.txt`，并在当前 Anbennar 的 `common/diplomatic_actions/00_diplomatic_actions.txt`、`events/Flavour_Gawed_A13.txt` 中插入改革接口。与修改相同文件的其他模组需要合并；不覆盖决议界面或顶栏。Anbennar 更新后可用 `tools/build_reform_compat.py` 重建两份改革兼容文件，保留其余原有内容。逐处修改及待办见 [任务修正说明](制作源文件/加韦德任务_修正说明.md)。

尚未指定本项目的开源许可证。EU4、Anbennar 及第三方资源的权利归各自权利人所有。
