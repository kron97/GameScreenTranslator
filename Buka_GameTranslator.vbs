Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

If fso.FileExists(scriptDir & "\python_env\pythonw.exe") Then
    WshShell.Run """" & scriptDir & "\python_env\pythonw.exe"" """ & scriptDir & "\app.py""", 0, False
Else
    WshShell.Run """" & scriptDir & "\python_env\python.exe"" """ & scriptDir & "\app.py""", 0, False
End If
