++++++++++++++
Instrument FOV
++++++++++++++

Instrument FOV 插件用于在 `<wsname>_FIND` 窗口中的巡天图像之上叠加仪器的
视场（FOV）。

.. note:: 为使本插件正常工作，重要的是事先（使用 “FindImage” 插件）已在
          查找查看器中下载了一幅具有精确 WCS 的图像。

选择仪器
========

可以通过按下 “Instrument” 下方的 “Choose” 按钮，然后浏览菜单直到找到所需
仪器来选择仪器。选定仪器后，其名称将填入 “Instrument:”，并且仪器视场的轮廓
将出现在 `<wsname>_FIND` 窗口中。

可以调整位置角，这将调整图像上仪器 FOV 叠加层的角度。如果勾选了 “Rotate
w/PA” 复选框，查看器图像将随之旋转，使 FOV 叠加层保持相同的方向。

在 `<wsname>_FIND` 窗口中设置平移位置（例如通过 Shift 单击）时，RA 和 DEC
将自动填充，但也可以通过输入坐标来手动调整。RA 和 DEC 可以指定为十进制值
（度）或六十进制表示法。

要将图像居中到当前望远镜指向，请在 ``FindImage`` 插件界面中勾选 “Follow
telescope” 旁边的复选框。如果查找图像中的 WCS 足够精确，这将使你能够观察
天空某个区域上正在发生的抖动。

.. note:: 要使 “Follow telescope” 功能正常工作，你需要按照 TelescopePosition
          插件文档中的说明，编写一个从望远镜获取状态的配套插件。
