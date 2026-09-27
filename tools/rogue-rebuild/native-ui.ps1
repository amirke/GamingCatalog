$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class JabuUI {
 public delegate bool Callback(IntPtr h,IntPtr p);
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int Left,Top,Right,Bottom;}
 [DllImport("user32.dll")] public static extern bool EnumWindows(Callback f,IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h,Callback f,IntPtr p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,StringBuilder b,int n);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,StringBuilder b,int n);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr h);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
 [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr h);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,string l);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessageTimeout(IntPtr h,uint m,IntPtr w,StringBuilder l,uint flags,uint timeout,out IntPtr result);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern IntPtr VirtualAllocEx(IntPtr p,IntPtr a,UIntPtr size,uint type,uint protect);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool WriteProcessMemory(IntPtr p,IntPtr a,byte[] bytes,UIntPtr size,out UIntPtr written);
 [DllImport("kernel32.dll")] public static extern bool VirtualFreeEx(IntPtr p,IntPtr a,UIntPtr size,uint type);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr p);
 [DllImport("user32.dll",EntryPoint="SendMessageW")] private static extern IntPtr SendPointer(IntPtr h,uint m,IntPtr w,IntPtr l);
 public static void SelectFolder(IntPtr dialog,string path){
  if(Class(dialog)!="#32770" || Text(dialog)!="Browse For Folder")throw new Exception("Unexpected folder dialog");
  var name=System.Diagnostics.Process.GetProcessById((int)Pid(dialog)).ProcessName;
  if(name!="PS2-FPKG")throw new Exception("Not a Jabu dialog");
  // BFFM_SETSELECTIONW is above WM_USER: Windows does not marshal its string across processes.
  var bytes=Encoding.Unicode.GetBytes(path+"\0");var p=OpenProcess(0x28,false,Pid(dialog));if(p==IntPtr.Zero)throw new Exception("OpenProcess failed");
  var a=IntPtr.Zero;
  try{a=VirtualAllocEx(p,IntPtr.Zero,(UIntPtr)bytes.Length,0x3000,4);UIntPtr written;
   if(a==IntPtr.Zero || !WriteProcessMemory(p,a,bytes,(UIntPtr)bytes.Length,out written) || written.ToUInt64()!=(ulong)bytes.Length)throw new Exception("Cannot marshal folder path");
   SendPointer(dialog,0x467,(IntPtr)1,a);
  }finally{if(a!=IntPtr.Zero)VirtualFreeEx(p,a,UIntPtr.Zero,0x8000);CloseHandle(p);}
 }
 public static string Text(IntPtr h){var b=new StringBuilder(4096);IntPtr result;SendMessageTimeout(h,13,(IntPtr)b.Capacity,b,2,1000,out result);return b.ToString();}
 public static string Class(IntPtr h){var b=new StringBuilder(256);GetClassName(h,b,b.Capacity);return b.ToString();}
 public static uint Pid(IntPtr h){uint p;GetWindowThreadProcessId(h,out p);return p;}
 public static IntPtr[] Tops(){var a=new List<IntPtr>();EnumWindows((h,p)=>{a.Add(h);return true;},IntPtr.Zero);return a.ToArray();}
 public static IntPtr[] Children(IntPtr h){var a=new List<IntPtr>();EnumChildWindows(h,(w,p)=>{a.Add(w);return true;},IntPtr.Zero);return a.ToArray();}
}
'@
function Get-JabuWindows {
 $ids=@((Get-Process -Name PS2-FPKG -ErrorAction SilentlyContinue).Id)
 foreach($h in [JabuUI]::Tops()){if([JabuUI]::Pid($h) -in $ids -and [JabuUI]::IsWindowVisible($h)){$h}}
}
function Get-JabuNodes([IntPtr]$Window){
 foreach($h in @($Window)+[JabuUI]::Children($Window)){
  $r=New-Object JabuUI+Rect;[void][JabuUI]::GetWindowRect($h,[ref]$r)
  [pscustomobject]@{Handle=$h.ToInt64();Parent=[JabuUI]::GetParent($h).ToInt64();Id=[JabuUI]::GetDlgCtrlID($h);Text=[JabuUI]::Text($h);Class=[JabuUI]::Class($h);Enabled=[JabuUI]::IsWindowEnabled($h);Visible=[JabuUI]::IsWindowVisible($h);X=$r.Left;Y=$r.Top;Width=$r.Right-$r.Left;Height=$r.Bottom-$r.Top}
 }
}
function Save-JabuScreenshot([IntPtr]$Window,[string]$Path){
 $r=New-Object JabuUI+Rect;[void][JabuUI]::GetWindowRect($Window,[ref]$r)
 $b=New-Object System.Drawing.Bitmap ($r.Right-$r.Left),($r.Bottom-$r.Top)
 $g=[System.Drawing.Graphics]::FromImage($b);$dc=$g.GetHdc()
 try{[void][JabuUI]::PrintWindow($Window,$dc,2)}finally{$g.ReleaseHdc($dc);$g.Dispose()}
 $b.Save($Path,[System.Drawing.Imaging.ImageFormat]::Png);$b.Dispose()
}
