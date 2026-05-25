Set WshShell = CreateObject("WScript.Shell")
' 0 = ventana oculta
' False = no esperar a que termine
WshShell.Run "iniciar.bat", 0, False
Set WshShell = Nothing
