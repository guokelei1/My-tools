# context-menu-runner

`context-menu-runner` 是一个最小可用的 Windows 右键菜单工具骨架。

它的目标是：

- 在 Windows 资源管理器右键菜单里增加一个入口
- 点击后触发固定安装目录中的 launcher
- launcher 再调用 Python 主程序
- Python 主程序再执行你定义的 Bash 命令

这版实现已经按“固定运行目录”思路落地：

- 仓库目录是源码目录
- `%USERPROFILE%\menu\context-menu-runner\` 是稳定安装目录
- 注册表永远只指向安装目录，不指向当前仓库

---

## 当前已实现内容

当前目录已经包含这些文件：

- `install-context-menu.ps1`
- `uninstall-context-menu.ps1`
- `launcher/run-context.cmd`
- `app/main.py`
- `app/context.py`
- `app/executor.py`
- `app/backends.py`
- `app/config.py`
- `actions/default_action.py`

当前是“最小可用骨架”，适合先试通整条链路。

---

## 整个调用链

这版实现的调用链是固定的：

```text
仓库目录
  -> install-context-menu.ps1
  -> 复制程序到 %USERPROFILE%\menu\context-menu-runner\
  -> 写入 HKCU 右键菜单

Explorer 右键
  -> 注册表菜单项
  -> %USERPROFILE%\menu\context-menu-runner\launcher\run-context.cmd
  -> %USERPROFILE%\menu\context-menu-runner\app\main.py
  -> %USERPROFILE%\menu\context-menu-runner\actions\default_action.py
  -> Git Bash / WSL
  -> logs
```

也就是说：

- 右键不直接运行 repo 里的代码
- 右键只运行安装目录里的副本

---

## 为什么要安装到 `%USERPROFILE%\menu`

因为仓库路径不稳定：

- 你可能会移动仓库
- 你可能会改目录名
- 你可能会删除仓库重新 clone

如果注册表直接指向仓库目录，右键菜单迟早失效。

而固定安装到：

- `%USERPROFILE%\menu\context-menu-runner\`

之后，右键菜单依赖的是稳定运行目录，不再依赖源码目录位置。

---

## install 脚本做什么

运行：

```powershell
.\install-context-menu.ps1
```

它会做这几件事：

1. 校验源码文件是否完整
2. 把 `launcher/`、`app/`、`actions/` 复制到 `%USERPROFILE%\menu\context-menu-runner\`
3. 创建 `%USERPROFILE%\menu\context-menu-runner\logs\`
4. 写入 `install-metadata.json`
5. 在当前用户注册表写入两个右键入口

注册表入口当前包括：

- 右键某个文件夹
- 在文件夹空白处右键

写入位置是：

- `HKCU\Software\Classes\Directory\shell\MyTools.ContextMenuRunner`
- `HKCU\Software\Classes\Directory\Background\shell\MyTools.ContextMenuRunner`

---

## uninstall 脚本做什么

运行：

```powershell
.\uninstall-context-menu.ps1
```

默认行为：

- 删除右键菜单注册表项
- 保留 `%USERPROFILE%\menu\context-menu-runner\` 运行目录

如果你要彻底清理安装目录，可以运行：

```powershell
.\uninstall-context-menu.ps1 -RemoveInstalledFiles
```

这样会：

- 删注册表
- 删 `%USERPROFILE%\menu\context-menu-runner\`

默认不删安装目录，是为了保留：

- 你可能改过的动作文件
- 运行日志

---

## launcher 做什么

`launcher/run-context.cmd` 是注册表唯一指向的入口。

它负责：

- 找到安装目录中的 `app/main.py`
- 优先使用 `%USERPROFILE%\menu\context-menu-runner\.venv\Scripts\python.exe`
- 找不到时回退到 `py -3`
- 再找不到时回退到 `python`
- 把右键传进来的参数转给 Python

如果 Python 没找到，launcher 会报错并停住窗口，方便排错。

---

## Python 主程序做什么

`app/main.py` 做的事情比较简单：

1. 解析 `--mode` 和 `--target`
2. 构造统一的 `InvocationContext`
3. 加载 `actions/default_action.py`
4. 要求动作文件返回 `ActionSpec`
5. 把动作交给执行器运行

当前支持的 `mode` 值包括：

- `directory`
- `background`
- `file`
- `multi`

虽然当前注册表只先接了 `directory` 和 `background`，但 Python 入口已经给后续扩展留了位置。

---

## 动作文件怎么改

你以后最常改的文件是：

- `actions/default_action.py`

这个文件当前暴露：

- `build_action(context)`

它必须返回一个 `ActionSpec`，其中包括：

- 动作名
- 命令列表
- shell backend
- 工作目录
- 超时设置

当前默认动作现在会在目标目录执行三条 Git 命令：

- `git add .`
- `git commit -m "new commit"`
- `git push`

右键菜单显示名称是：

- `git autocmd`

成功执行后由 launcher 让终端窗口额外停留 `5` 秒。

---

## Bash 后端怎么选

执行层当前支持这些后端：

- `bash`
- `wsl`
- `powershell`

默认动作当前使用：

- `auto-bash`

这意味着它会优先找：

1. Git Bash 或系统里的 `bash.exe`
2. `wsl.exe`

如果两个都没有，会直接报错，而不是偷偷用别的执行器。

这样更符合“我就是要执行 Bash 命令”的预期。

---

## 日志写到哪里

每次运行都会把日志写到：

- `%USERPROFILE%\menu\context-menu-runner\logs\`

日志文件名形如：

- `20260324-170800-default-action.log`

日志里会记录：

- 动作名
- 实际后端
- 工作目录
- 实际执行命令
- stdout/stderr
- 退出码

---

## 现在应该怎么使用

### 第一次安装

在仓库目录执行：

```powershell
.\tools\context-menu-runner\install-context-menu.ps1
```

或进入目录后执行：

```powershell
.\install-context-menu.ps1
```

### 运行

安装成功后，到 Explorer 中：

- 右键某个文件夹
- 或在目录空白处右键

点击：

- `Run My Bash Tool`

### 更新

如果你修改了源码里的：

- `actions/default_action.py`
- `app/*.py`
- `launcher/run-context.cmd`

修改后重新跑一次：

```powershell
.\install-context-menu.ps1
```

它会重新把新版本复制到 `%USERPROFILE%\menu\context-menu-runner\`。

### 卸载

```powershell
.\uninstall-context-menu.ps1
```

如果要连安装目录一起删：

```powershell
.\uninstall-context-menu.ps1 -RemoveInstalledFiles
```

---

## 以后怎么迁移

### 迁移仓库目录

如果你只是移动当前仓库目录，通常不影响右键菜单，因为右键实际调用的是：

- `%USERPROFILE%\menu\context-menu-runner\`

### 迁移安装目录

如果你以后想换安装根目录，正确流程是：

1. 先运行 `uninstall-context-menu.ps1`
2. 调整 install 脚本里的安装路径策略
3. 重新运行 `install-context-menu.ps1`

也就是说：

- 仓库可以移动
- 运行目录不要直接手动乱挪

---

## 一个很重要的注意点

当前 `install-context-menu.ps1` 会覆盖安装目录中的：

- `launcher/`
- `app/`
- `actions/`

所以如果你直接手改了：

- `%USERPROFILE%\menu\context-menu-runner\actions\default_action.py`

下次重新安装时会被源码版本覆盖。

因此推荐的习惯是：

- 改仓库里的源码
- 然后重新执行 install

不要把安装目录当成长期唯一源码目录。

---

## 当前限制

这版是最小骨架，所以也有边界：

- 当前右键只接了文件夹和目录空白处
- 当前只有一个动作文件 `actions/default_action.py`
- 当前没有多动作子菜单
- 当前没有 YAML/JSON 动作配置
- 当前没有图标定制
- 当前没有执行前确认框

但整条主链路已经可以继续往上扩展了。

---

## 下一步最适合做什么

如果继续增强，最自然的下一步是：

1. 增加多动作菜单
2. 支持外部动作目录
3. 支持 YAML/JSON 配置
4. 增加文件右键和多选支持
5. 增加更清晰的失败提示
