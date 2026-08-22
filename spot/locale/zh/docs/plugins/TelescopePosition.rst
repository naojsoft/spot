++++++++++++++++++
Telescope Position
++++++++++++++++++

TelescopePosition 插件显示望远镜的实时位置和指令（目标）位置。

.. note:: 为了成功使用本插件，需要编写一个自定义的配套插件来提供绘制这些
          位置所需的状态。如果你没有创建这样的插件，看起来就会像是望远镜
          处于停放状态。

望远镜和目标位置同时以赤经/赤纬和方位角/高度角显示。RA 和 DEC 以六十进制
表示法显示，RA 为 HH:MM:SS.SSS，DEC 为 DD:MM:SS.SS。AZ 和 EL 均以十进制值
的度显示。在 “Telescope” 部分，会显示望远镜状态（如指向或转向），以及以
h:mm:ss 表示的转向时间。

勾选 “Plot telescope position” 选项后，将在 Targets 窗口上显示目标和望远镜
的位置。

“Target follow telescope” 选项会在望远镜“接近”某个目标时（“接近”定义为大约
在 10 角分以内），使该目标在 Targets 插件表中被选中。将选中实际上离望远镜
坐标最近的目标。

.. note:: 如果在勾选此框后用户手动选择了某个目标，该选项将自动取消勾选。要
          恢复目标跟随望远镜，只需重新勾选该框即可。

“Pan to telescope position” 选项会使 TGTS 查看器平移到望远镜位置。当绘制了
大量目标并且你已放大以仅显示极坐标天空场的一部分时，这会很有帮助。

编写配套插件
============

下载 SPOT 源代码，在 “spot/examples” 文件夹中查找名为
“TelescopePosition_Companion” 的插件模板。按模板中的说明进行修改。
