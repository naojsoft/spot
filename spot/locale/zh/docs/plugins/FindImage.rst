FindImage
=========
FindImage 插件用于针对已知坐标，从图像目录下载并显示图像。它使用
“{wsname}_FIND” 查看器来显示找到的图像。

.. note:: 请确保同时打开 “Targets” 插件，因为它需要与本插件配合使用。

选择目标
--------
在 “Targets” 插件中选择单个目标以唯一地选定它。然后单击 FindImage 中
“Pointing” 区域的 “Get Selected” 按钮。这将填充 “RA”、“DEC”、“Equinox” 和
“Name” 字段。

.. note:: 如果你有可用的望远镜状态集成，可以勾选 “Follow telescope”
          复选框，让 “Pointing” 区域根据望远镜的实际位置更新（前提是它与
          已加载到 Targets 插件中的某个目标匹配）。此外，查找查看器中的
          图像将根据望远镜的当前位置下载并平移，从而使你能够（例如）跟随
          抖动模式。

从图像源加载图像
----------------
一旦 RA/DEC 坐标显示在 “Pointing” 区域，就可以使用 “Image Source” 区域的
控件下载图像。从标有 “Source” 的下拉控件中选择图像源，使用 “Size” 控件选择
大小（以角分为单位），然后单击 “Find Image” 按钮。图像下载并显示在查找查看器
中可能需要一些时间。

.. note:: 或者，可以使用 “Load FITS” 加载该区域带有可用 WCS 的本地 FITS
          文件，或者单击 “Create Blank” 创建一个 WCS 设置到所需位置的空白
          图像。当无法通过下载获得图像源时，这两种方法之一可能会很有用。
