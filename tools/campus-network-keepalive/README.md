# Campus Network Keep-Alive 校园网保活工具

一个轻量级的Windows后台服务，用于监控和保持Ruijie Supplicant (锐捷认证客户端) 持续运行，防止校园网意外断开。

## 功能特性

✅ **自动启动** - Windows开机时自动运行
✅ **持续监控** - 每30秒检查一次Ruijie Supplicant是否运行
✅ **自动重启** - 如果应用关闭，自动重新启动
✅ **定时启动** - 每隔1小时再启动一次，保持连接活跃
✅ **详细日志** - 记录所有操作到日志文件
✅ **零占用** - 当应用正常运行时几乎不占用资源

## 安装步骤

### 1. 准备工作

确保您已经安装了 **Ruijie Supplicant** (锐捷认证客户端)：
- 默认安装路径: `C:\Program Files\Ruijie Networks\Ruijie Supplicant\RuijieSupplicant.exe`
- 如果安装在其他位置，需要修改脚本中的路径

### 2. 安装服务

1. **右键点击 PowerShell** → 选择 **"以管理员身份运行"**（重要！）

2. **粘贴以下命令**并回车：
   ```powershell
   cd "C:\Users\Administrator\Desktop\My-tools\tools\campus-network-keepalive"
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
   .\install.ps1
   ```

3. 等待显示 "Installation complete!" 表示安装成功

### 3. 验证安装

安装完成后，您会看到：
- 一个名为 "RuijieKeepAlive" 的计划任务被创建
- 它会在 Windows 启动时自动运行

验证方式：
```powershell
Get-ScheduledTask -TaskName RuijieKeepAlive
```

## 查看日志

所有操作日志都保存在：
```
%APPDATA%\RuijieKeepAlive\log.txt
```

即：`C:\Users\[YourUsername]\AppData\Roaming\RuijieKeepAlive\log.txt`

快速查看日志：
```powershell
notepad $env:APPDATA\RuijieKeepAlive\log.txt
```

## 卸载服务

如果需要停止使用此服务，以管理员身份运行：

```powershell
cd "C:\Users\Administrator\Desktop\My-tools\tools\campus-network-keepalive"
.\uninstall.ps1
```

## 工作原理

1. **任务计划** - Windows 任务计划程序在以下情况下启动此脚本：
   - Windows 系统启动时
   - 每分钟自动运行一次（作为备份）

2. **监控循环** - 脚本进入无限循环，每30秒执行一次检查：
   - 检查 RuijieSupplicant.exe 进程是否存在
   - 如果不存在，立即启动它
   - 记录所有操作到日志文件

3. **定时启动** - 自动在以下情况下启动Ruijie：
   - **应急启动**：进程意外关闭时（30秒内自动启动）
   - **定时启动**：每隔1小时再启动一次，保持校园网连接活跃

4. **持久保活** - 脚本始终在后台运行，确保：
   - 即使用户不小心关闭了应用
   - 即使应用自己崩溃
   - 校园网连接也始终保持活跃

## 常见问题

### Q: 可以修改检查间隔吗？
可以，编辑 `RuijieKeepAlive.ps1` 第35行的 `Start-Sleep -Seconds 30` 改成其他数值（单位：秒）。

### Q: 如果Ruijie安装在非默认路径？
编辑 `RuijieKeepAlive.ps1` 第7行修改路径：
```powershell
$RuijieExePath = "你的实际安装路径"
```

### Q: 怎么确认它在运行？
查看日志文件：
```powershell
Get-Content $env:APPDATA\RuijieKeepAlive\log.txt -Tail 20
```

### Q: 可以从任务计划程序手动启动吗？
可以，打开"任务计划程序"(taskschd.msc) → 找到 "RuijieKeepAlive" → 右键 "运行"

## 技术细节

- **运行权限**: SYSTEM (系统账户，具有最高权限)
- **运行方式**: 后台隐藏窗口，不会显示命令行窗口
- **监控方式**: 检查进程名称 "RuijieSupplicant"
- **日志位置**: 用户AppData目录（任何用户都可以访问）

## 注意事项

⚠️ **必须以管理员身份运行安装脚本**
⚠️ 如果修改了脚本，需要重新运行 `install.ps1` 才能生效
⚠️ 卸载后需要手动重新启动Ruijie Supplicant

## 许可证

自由使用，无任何限制。
