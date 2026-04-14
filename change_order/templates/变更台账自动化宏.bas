' ============================================
' 变更台账自动化工具 - VBA 宏代码
' 渝中区污水溢流整治项目
' ============================================
' 功能清单：
' 1. 一键生成周报
' 2. 一键生成月报
' 3. 自动邮件提醒
' 4. 数据自动备份
' 5. 预警自动刷新
' ============================================

Option Explicit

' ============================================
' 模块 1: 报表生成
' ============================================

' --- 生成周报 ---
Sub 生成周报 ()
    Dim ws 台账 As Worksheet
    Dim ws 周报 As Worksheet
    Dim 本周开始 As Date, 本周结束 As Date
    Dim 行号 As Long, 周报行 As Long
    Dim 新增数量 As Integer, 批准数量 As Integer
    Dim 申报总额 As Double, 批准总额 As Double
    
    ' 设置工作表
    Set ws 台账 = ThisWorkbook.Sheets("1️⃣台账总表")
    
    ' 检查周报工作表是否存在
    On Error Resume Next
    Set ws 周报 = ThisWorkbook.Sheets("周报")
    On Error GoTo 0
    
    If ws 周报 Is Nothing Then
        Set ws 周报 = ThisWorkbook.Sheets.Add(After:=ws 台账)
        ws 周报.Name = "周报"
    End If
    
    ' 计算本周日期范围
    本周开始 = Date - Weekday(Date, vbMonday) + 1
    本周结束 = 本周开始 + 6
    
    ' 清空周报内容
    ws 周报.Cells.Clear
    
    ' 写入周报标题
    ws 周报.Range("A1").Value = "变更签证周报"
    ws 周报.Range("A2").Value = "统计期间：" & Format(本周开始，"yyyy-mm-dd") & " ~ " & Format(本周结束，"yyyy-mm-dd")
    ws 周报.Range("A3").Value = "生成时间：" & Now()
    
    ' 设置标题格式
    With ws 周报.Range("A1")
        .Font.Size = 16
        .Font.Bold = True
        .HorizontalAlignment = xlCenter
    End With
    
    ' 统计本周数据
    新增数量 = 统计本周新增 (ws 台账，本周开始，本周结束)
    批准数量 = 统计本周批准 (ws 台账，本周开始，本周结束)
    申报总额 = 统计本周申报金额 (ws 台账，本周开始，本周结束)
    批准总额 = 统计本周批准金额 (ws 台账，本周开始，本周结束)
    
    ' 写入概况
    ws 周报.Range("A5").Value = "【本周概况】"
    ws 周报.Range("A6").Value = "新增变更：" & 新增数量 & " 笔"
    ws 周报.Range("A7").Value = "批准变更：" & 批准数量 & " 笔"
    ws 周报.Range("A8").Value = "申报金额：" & Format(申报总额，"¥#,##0.00")
    ws 周报.Range("A9").Value = "批准金额：" & Format(批准总额，"¥#,##0.00")
    
    ' 生成预警清单
    生成预警清单 ws 台账，ws 周报，15
    
    ' 生成证据缺失清单
    生成证据缺失清单 ws 台账，ws 周报，15
    
    ' 自动调整列宽
    ws 周报.Columns.AutoFit
    
    ' 提示
    MsgBox "周报已生成！" & vbCrLf & _
           "统计期间：" & Format(本周开始，"yyyy-mm-dd") & " ~ " & Format(本周结束，"yyyy-mm-dd") & vbCrLf & _
           "新增变更：" & 新增数量 & " 笔" & vbCrLf & _
           "批准变更：" & 批准数量 & " 笔", vbInformation, "周报生成完成"
    
End Sub

' --- 生成月报 ---
Sub 生成月报 ()
    Dim ws 台账 As Worksheet
    Dim ws 月报 As Worksheet
    Dim 月初 As Date, 月末 As Date
    Dim 新增数量 As Integer, 批准数量 As Integer
    Dim 申报总额 As Double, 批准总额 As Double
    Dim 累计金额 As Double
    
    ' 设置工作表
    Set ws 台账 = ThisWorkbook.Sheets("1️⃣台账总表")
    
    ' 检查月报工作表是否存在
    On Error Resume Next
    Set ws 月报 = ThisWorkbook.Sheets("月报")
    On Error GoTo 0
    
    If ws 月报 Is Nothing Then
        Set ws 月报 = ThisWorkbook.Sheets.Add(After:=ws 台账)
        ws 月报.Name = "月报"
    End If
    
    ' 计算本月日期范围
    月初 = DateSerial(Year(Date), Month(Date), 1)
    月末 = DateSerial(Year(Date), Month(Date) + 1, 0)
    
    ' 清空月报内容
    ws 月报.Cells.Clear
    
    ' 写入月报标题
    ws 月报.Range("A1").Value = "变更签证月报"
    ws 月报.Range("A2").Value = "统计期间：" & Format(月初，"yyyy 年 MM 月")
    ws 月报.Range("A3").Value = "生成时间：" & Now()
    
    ' 设置标题格式
    With ws 月报.Range("A1")
        .Font.Size = 16
        .Font.Bold = True
        .HorizontalAlignment = xlCenter
    End With
    
    ' 统计本月数据
    新增数量 = 统计本月新增 (ws 台账，月初，月末)
    批准数量 = 统计本月批准 (ws 台账，月初，月末)
    申报总额 = 统计本月申报金额 (ws 台账，月初，月末)
    批准总额 = 统计本月批准金额 (ws 台账，月初，月末)
    
    ' 统计累计数据
    累计金额 = 统计累计金额 (ws 台账)
    
    ' 写入概况
    ws 月报.Range("A5").Value = "【本月概况】"
    ws 月报.Range("A6").Value = "新增变更：" & 新增数量 & " 笔"
    ws 月报.Range("A7").Value = "批准变更：" & 批准数量 & " 笔"
    ws 月报.Range("A8").Value = "申报金额：" & Format(申报总额，"¥#,##0.00")
    ws 月报.Range("A9").Value = "批准金额：" & Format(批准总额，"¥#,##0.00")
    ws 月报.Range("A10").Value = "累计金额：" & Format(累计金额，"¥#,##0.00")
    
    ' 生成类型分布
    生成类型分布 ws 台账，ws 月报，12
    
    ' 生成原因分布
    生成原因分布 ws 台账，ws 月报，12
    
    ' 自动调整列宽
    ws 月报.Columns.AutoFit
    
    ' 提示
    MsgBox "月报已生成！" & vbCrLf & _
           "统计期间：" & Format(月初，"yyyy 年 MM 月") & vbCrLf & _
           "新增变更：" & 新增数量 & " 笔" & vbCrLf & _
           "累计金额：" & Format(累计金额，"¥#,##0.00"), vbInformation, "月报生成完成"
    
End Sub

' ============================================
' 模块 2: 统计函数
' ============================================

' --- 统计本周新增 ---
Function 统计本周新增 (ws As Worksheet, 开始日期 As Date, 结束日期 As Date) As Integer
    Dim i As Long, 计数 As Integer
    Dim 申报日期 As Date
    
    计数 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "E").Value) Then
            申报日期 = ws.Cells(i, "E").Value
            If 申报日期 >= 开始日期 And 申报日期 <= 结束日期 Then
                计数 = 计数 + 1
            End If
        End If
    Next i
    
    统计本周新增 = 计数
End Function

' --- 统计本周批准 ---
Function 统计本周批准 (ws As Worksheet, 开始日期 As Date, 结束日期 As Date) As Integer
    Dim i As Long, 计数 As Integer
    Dim 审批日期 As Date
    
    计数 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "M").Value) Then
            审批日期 = ws.Cells(i, "M").Value
            If 审批日期 >= 开始日期 And 审批日期 <= 结束日期 Then
                If ws.Cells(i, "L").Value = "已批" Then
                    计数 = 计数 + 1
                End If
            End If
        End If
    Next i
    
    统计本周批准 = 计数
End Function

' --- 统计本周申报金额 ---
Function 统计本周申报金额 (ws As Worksheet, 开始日期 As Date, 结束日期 As Date) As Double
    Dim i As Long, 金额 As Double
    Dim 申报日期 As Date
    
    金额 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "E").Value) Then
            申报日期 = ws.Cells(i, "E").Value
            If 申报日期 >= 开始日期 And 申报日期 <= 结束日期 Then
                If IsNumeric(ws.Cells(i, "H").Value) Then
                    金额 = 金额 + ws.Cells(i, "H").Value
                End If
            End If
        End If
    Next i
    
    统计本周申报金额 = 金额
End Function

' --- 统计本周批准金额 ---
Function 统计本周批准金额 (ws As Worksheet, 开始日期 As Date, 结束日期 As Date) As Double
    Dim i As Long, 金额 As Double
    Dim 审批日期 As Date
    
    金额 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "M").Value) Then
            审批日期 = ws.Cells(i, "M").Value
            If 审批日期 >= 开始日期 And 审批日期 <= 结束日期 Then
                If ws.Cells(i, "L").Value = "已批" Then
                    If IsNumeric(ws.Cells(i, "I").Value) Then
                        金额 = 金额 + ws.Cells(i, "I").Value
                    End If
                End If
            End If
        End If
    Next i
    
    统计本周批准金额 = 金额
End Function

' --- 统计本月新增 ---
Function 统计本月新增 (ws As Worksheet, 月初 As Date, 月末 As Date) As Integer
    Dim i As Long, 计数 As Integer
    Dim 申报日期 As Date
    
    计数 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "E").Value) Then
            申报日期 = ws.Cells(i, "E").Value
            If 申报日期 >= 月初 And 申报日期 <= 月末 Then
                计数 = 计数 + 1
            End If
        End If
    Next i
    
    统计本月新增 = 计数
End Function

' --- 统计本月批准 ---
Function 统计本月批准 (ws As Worksheet, 月初 As Date, 月末 As Date) As Integer
    Dim i As Long, 计数 As Integer
    Dim 审批日期 As Date
    
    计数 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "M").Value) Then
            审批日期 = ws.Cells(i, "M").Value
            If 审批日期 >= 月初 And 审批日期 <= 月末 Then
                If ws.Cells(i, "L").Value = "已批" Then
                    计数 = 计数 + 1
                End If
            End If
        End If
    Next i
    
    统计本月批准 = 计数
End Function

' --- 统计本月申报金额 ---
Function 统计本月申报金额 (ws As Worksheet, 月初 As Date, 月末 As Date) As Double
    Dim i As Long, 金额 As Double
    Dim 申报日期 As Date
    
    金额 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "E").Value) Then
            申报日期 = ws.Cells(i, "E").Value
            If 申报日期 >= 月初 And 申报日期 <= 月末 Then
                If IsNumeric(ws.Cells(i, "H").Value) Then
                    金额 = 金额 + ws.Cells(i, "H").Value
                End If
            End If
        End If
    Next i
    
    统计本月申报金额 = 金额
End Function

' --- 统计本月批准金额 ---
Function 统计本月批准金额 (ws As Worksheet, 月初 As Date, 月末 As Date) As Double
    Dim i As Long, 金额 As Double
    Dim 审批日期 As Date
    
    金额 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsDate(ws.Cells(i, "M").Value) Then
            审批日期 = ws.Cells(i, "M").Value
            If 审批日期 >= 月初 And 审批日期 <= 月末 Then
                If ws.Cells(i, "L").Value = "已批" Then
                    If IsNumeric(ws.Cells(i, "I").Value) Then
                        金额 = 金额 + ws.Cells(i, "I").Value
                    End If
                End If
            End If
        End If
    Next i
    
    统计本月批准金额 = 金额
End Function

' --- 统计累计金额 ---
Function 统计累计金额 (ws As Worksheet) As Double
    Dim i As Long, 金额 As Double
    
    金额 = 0
    For i = 2 To ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
        If IsNumeric(ws.Cells(i, "H").Value) Then
            金额 = 金额 + ws.Cells(i, "H").Value
        End If
    Next i
    
    统计累计金额 = 金额
End Function

' ============================================
' 模块 3: 清单生成
' ============================================

' --- 生成预警清单 ---
Sub 生成预警清单 (ws 台账 As Worksheet, ws 输出 As Worksheet, 起始行 As Integer)
    Dim i As Long, 输出行 As Integer
    Dim 超时天数 As Integer
    Dim 预警级别 As String
    
    输出行 = 起始行 + 5
    ws 输出.Cells(输出行 - 2, "A").Value = "【预警事项清单】"
    ws 输出.Cells(输出行 - 1, "A").Value = "变更编号 | 变更名称 | 超时天数 | 预警级别 | 责任人"
    
    For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
        超时天数 = ws 台账.Cells(i, "O").Value
        预警级别 = ws 台账.Cells(i, "P").Value
        
        If 超时天数 > 7 Or 预警级别 Like "*预警*" Or 预警级别 Like "*警报*" Then
            ws 输出.Cells(输出行，"A").Value = ws 台账.Cells(i, "B").Value & " | " & _
                                              ws 台账.Cells(i, "C").Value & " | " & _
                                              超时天数 & "天 | " & _
                                              预警级别 & " | " & _
                                              ws 台账.Cells(i, "U").Value
            输出行 = 输出行 + 1
        End If
    Next i
End Sub

' --- 生成证据缺失清单 ---
Sub 生成证据缺失清单 (ws 台账 As Worksheet, ws 输出 As Worksheet, 起始行 As Integer)
    Dim i As Long, 输出行 As Integer
    Dim 证据分 As Integer
    Dim 证据等级 As String
    
    输出行 = 起始行 + 15
    ws 输出.Cells(输出行 - 2, "A").Value = "【证据缺失清单】"
    ws 输出.Cells(输出行 - 1, "A").Value = "变更编号 | 变更名称 | 证据分 | 证据等级 | 责任人"
    
    For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
        证据分 = ws 台账.Cells(i, "Q").Value
        证据等级 = ws 台账.Cells(i, "R").Value
        
        If 证据分 < 70 Or 证据等级 Like "*缺失*" Or 证据等级 Like "*高风险*" Then
            ws 输出.Cells(输出行，"A").Value = ws 台账.Cells(i, "B").Value & " | " & _
                                              ws 台账.Cells(i, "C").Value & " | " & _
                                              证据分 & "分 | " & _
                                              证据等级 & " | " & _
                                              ws 台账.Cells(i, "U").Value
            输出行 = 输出行 + 1
        End If
    Next i
End Sub

' --- 生成类型分布 ---
Sub 生成类型分布 (ws 台账 As Worksheet, ws 输出 As Worksheet, 起始行 As Integer)
    Dim 类型 As Variant
    Dim i As Long, 输出行 As Integer
    Dim 计数 As Integer, 金额 As Double
    
    类型 = Array("A 类重大", "B 类较大", "C 类一般", "D 类微小")
    输出行 = 起始行 + 5
    
    ws 输出.Cells(输出行 - 2, "A").Value = "【变更类型分布】"
    ws 输出.Cells(输出行 - 1, "A").Value = "类型 | 数量 | 金额"
    
    For Each 类型 In 类型
        计数 = 0
        金额 = 0
        
        For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
            If ws 台账.Cells(i, "D").Value = 类型 Then
                计数 = 计数 + 1
                If IsNumeric(ws 台账.Cells(i, "H").Value) Then
                    金额 = 金额 + ws 台账.Cells(i, "H").Value
                End If
            End If
        Next i
        
        ws 输出.Cells(输出行，"A").Value = 类型 & " | " & 计数 & " | " & Format(金额，"¥#,##0.00")
        输出行 = 输出行 + 1
    Next 类型
End Sub

' --- 生成原因分布 ---
Sub 生成原因分布 (ws 台账 As Worksheet, ws 输出 As Worksheet, 起始行 As Integer)
    Dim 原因 As Variant
    Dim i As Long, 输出行 As Integer
    Dim 计数 As Integer, 金额 As Double
    
    原因 = Array("管线冲突", "地质变化", "居民协调", "设计优化", "其他")
    输出行 = 起始行 + 15
    
    ws 输出.Cells(输出行 - 2, "A").Value = "【变更原因分布】"
    ws 输出.Cells(输出行 - 1, "A").Value = "原因 | 数量 | 金额"
    
    For Each 原因 In 原因
        计数 = 0
        金额 = 0
        
        For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
            If ws 台账.Cells(i, "G").Value = 原因 Then
                计数 = 计数 + 1
                If IsNumeric(ws 台账.Cells(i, "H").Value) Then
                    金额 = 金额 + ws 台账.Cells(i, "H").Value
                End If
            End If
        Next i
        
        ws 输出.Cells(输出行，"A").Value = 原因 & " | " & 计数 & " | " & Format(金额，"¥#,##0.00")
        输出行 = 输出行 + 1
    Next 原因
End Sub

' ============================================
' 模块 4: 邮件提醒
' ============================================

' --- 发送预警邮件 ---
Sub 发送预警邮件 ()
    Dim ws 台账 As Worksheet
    Dim OutlookApp As Object
    Dim MailItem As Object
    Dim 邮件内容 As String
    Dim i As Long
    Dim 预警数量 As Integer
    
    Set ws 台账 = ThisWorkbook.Sheets("1️⃣台账总表")
    
    ' 统计预警数量
    预警数量 = 0
    For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
        If ws 台账.Cells(i, "P").Value Like "*预警*" Or ws 台账.Cells(i, "P").Value Like "*警报*" Then
            预警数量 = 预警数量 + 1
        End If
    Next i
    
    If 预警数量 = 0 Then
        MsgBox "无预警事项，无需发送邮件", vbInformation, "提示"
        Exit Sub
    End If
    
    ' 创建 Outlook 对象
    On Error Resume Next
    Set OutlookApp = CreateObject("Outlook.Application")
    On Error GoTo 0
    
    If OutlookApp Is Nothing Then
        MsgBox "无法启动 Outlook，请检查是否已安装", vbExclamation, "错误"
        Exit Sub
    End If
    
    ' 创建邮件
    Set MailItem = OutlookApp.CreateItem(0)
    
    ' 构建邮件内容
    邮件内容 = "各位同事：" & vbCrLf & vbCrLf
    邮件内容 = 邮件内容 & "截至 " & Format(Now(), "yyyy-mm-dd hh:mm") & "，变更签证系统共有 " & 预警数量 & " 项预警事项，请及时处理。" & vbCrLf & vbCrLf
    邮件内容 = 邮件内容 & "预警清单：" & vbCrLf
    邮件内容 = 邮件内容 & "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" & vbCrLf
    
    For i = 2 To ws 台账.Cells(ws 台账.Rows.Count, "B").End(xlUp).Row
        If ws 台账.Cells(i, "P").Value Like "*预警*" Or ws 台账.Cells(i, "P").Value Like "*警报*" Then
            邮件内容 = 邮件内容 & "• " & ws 台账.Cells(i, "B").Value & " " & _
                                      ws 台账.Cells(i, "C").Value & " " & _
                                      "超时" & ws 台账.Cells(i, "O").Value & "天 " & _
                                      ws 台账.Cells(i, "P").Value & vbCrLf
        End If
    Next i
    
    邮件内容 = 邮件内容 & "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" & vbCrLf & vbCrLf
    邮件内容 = 邮件内容 & "请及时跟踪处理！" & vbCrLf & vbCrLf
    邮件内容 = 邮件内容 & "太一 AGI 系统 自动发送"
    
    ' 设置邮件属性
    With MailItem
        .To = "项目经理@company.com;商务经理@company.com"
        .Subject = "【预警提醒】变更签证预警事项 (" & 预警数量 & "项) - " & Format(Date, "yyyy-mm-dd")
        .Body = 邮件内容
        .Display ' 使用 Display 预览，如需自动发送改为.Send
    End With
    
    ' 清理
    Set MailItem = Nothing
    Set OutlookApp = Nothing
    
    MsgBox "邮件已生成，请检查 Outlook 发送队列", vbInformation, "邮件生成完成"
End Sub

' ============================================
' 模块 5: 数据备份
' ============================================

' --- 自动备份数据 ---
Sub 自动备份数据 ()
    Dim ws As Worksheet
    Dim 备份路径 As String
    Dim 备份文件名 As String
    Dim 源路径 As String
    
    ' 获取当前文件路径
    源路径 = ThisWorkbook.Path
    备份路径 = 源路径 & "\备份\"
    
    ' 创建备份文件夹
    On Error Resume Next
    MkDir 备份路径
    On Error GoTo 0
    
    ' 生成备份文件名
    备份文件名 = 备份路径 & "变更台账备份_" & Format(Now(), "yyyymmdd_hhmmss") & ".xlsx"
    
    ' 保存备份
    ThisWorkbook.SaveCopyAs 备份文件名
    
    ' 清理旧备份（保留最近 30 天）
    清理旧备份 备份路径，30
    
    MsgBox "数据已备份至：" & vbCrLf & 备份文件名, vbInformation, "备份完成"
End Sub

' --- 清理旧备份 ---
Sub 清理旧备份 (文件夹路径 As String, 保留天数 As Integer)
    Dim fso As Object
    Dim 文件 As Object
    Dim 文件时间 As Date
    Dim 删除日期 As Date
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    删除日期 = Date - 保留天数
    
    On Error Resume Next
    For Each 文件 In fso.GetFolder(文件夹路径).Files
        If 文件.Name Like "变更台账备份_*.xlsx" Then
            文件时间 = 文件.DateLastModified
            If 文件时间 < 删除日期 Then
                文件.Delete
            End If
        End If
    Next 文件
    On Error GoTo 0
    
    Set fso = Nothing
End Sub

' ============================================
' 模块 6: 快捷按钮
' ============================================

' --- 一键刷新所有 ---
Sub 一键刷新所有 ()
    ' 刷新所有公式
    Calculate
    
    ' 刷新所有数据透视表
    Dim pt As PivotTable
    For Each pt In ThisWorkbook.PivotTables
        pt.RefreshTable
    Next pt
    
    ' 刷新所有图表
    Dim ch As ChartObject
    For Each ch In ThisWorkbook.Charts
        ch.Chart.Refresh
    Next ch
    
    MsgBox "所有数据已刷新！" & vbCrLf & "时间：" & Format(Now(), "yyyy-mm-dd hh:mm:ss"), vbInformation, "刷新完成"
End Sub

' --- 一键导出 PDF ---
Sub 一键导出 PDF ()
    Dim 导出路径 As String
    Dim 文件名 As String
    
    导出路径 = ThisWorkbook.Path & "\导出\"
    
    ' 创建导出文件夹
    On Error Resume Next
    MkDir 导出路径
    On Error GoTo 0
    
    ' 生成文件名
    文件名 = 导出路径 & "变更台账_" & Format(Date, "yyyymmdd") & ".pdf"
    
    ' 导出 PDF
    ThisWorkbook.ExportAsFixedFormat Type:=xlTypePDF, _
                                     Filename:=文件名，_
                                     Quality:=xlQualityStandard, _
                                     IncludeDocProperties:=True, _
                                     IgnorePrintAreas:=False, _
                                     OpenAfterPublish:=True
    
    MsgBox "PDF 已导出至：" & vbCrLf & 文件名，vbInformation, "导出完成"
End Sub

' ============================================
' 模块 7: 自动任务（定时执行）
' ============================================

' --- 设置定时任务 ---
Sub 设置定时任务 ()
    ' 每天早上 9 点自动刷新
    Application.OnTime TimeValue("09:00:00"), "一键刷新所有"
    
    ' 每周五下午 5 点自动生成周报
    If Weekday(Date) = vbFriday Then
        Application.OnTime TimeValue("17:00:00"), "生成周报"
    End If
    
    ' 每月最后一个工作日下午 5 点自动生成月报
    If Day(Date) = Day(DateSerial(Year(Date), Month(Date) + 1, 0)) Then
        Application.OnTime TimeValue("17:00:00"), "生成月报"
    End If
    
    MsgBox "定时任务已设置！", vbInformation, "设置完成"
End Sub

' ============================================
' 结束
' ============================================
