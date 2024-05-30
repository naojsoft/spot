+++
RGB
+++

==========
Screenshot
==========
Capture PNG or JPEG images of the channel viewer image.

**Usage**

1. Select the RGB graphics type for the snap from the "Type" combo box.
2. Press "Snap" when you have the channel image the way you want to capture it.

A copy of the RGB image will be loaded into the ``ScreenShot`` viewer.
You can pan and zoom within the ``ScreenShot`` viewer like a normal Ginga
viewer to examine detail (e.g., see the magnified difference between
JPEG and PNG formats).

3. Repeat (1) and (2) until you have the image you want.
4. Enter a valid path for a new file into the "Folder" text box.
5. Enter a valid name for a new file into the "Name" text box.
   There is no need to add the file extension; it will be added, if needed.
6. Press the "Save" button.  The file will be saved where you specified.

**Notes**

* PNG offers less artifacts for overlaid graphics, but files are larger
  than JPEG.
* The "Center" button will center the snap image; "Fit" will set the
  zoom to fit it to the window; and "Clear" will clear the image.
  Press "Full" to zoom to 100% pixels (1:1 scaling).
* The "Screen size" checkbox (checked by default) will save the image at
  exactly the size of the channel viewer window.  To save at a different
  size, uncheck this box, and set the size via the "Width" and "Height"
  boxes.
* The "Lock aspect" feature only works if "Screen size" is unchecked; if
  enabled, then changing width or height will alter the other parameter
  in order to maintain the aspect ratio shown in the "Aspect" box.

==============
ColorMapPicker
==============
The ``ColorMapPicker`` plugin is used to graphically browse and select a
colormap for a channel image viewer.

**Plugin Type: Global or Local**

``ColorMapPicker`` is a hybrid global/local plugin, which means it can
be invoked in either fashion.  If invoked as a local plugin then it is
associated with a channel, and an instance can be opened for each channel.
It can also be opened as a global plugin.

**Usage**

Operation of the plugin is very simple: the colormaps are displayed in
the form of colorbars and labels in the main view pane of the plugin.
Click on any one of the bars to set the colormap of the associated
channel (if invoked as a local plugin) or the currently active channel
(if invoked as a global plugin).

You can scroll vertically or use the scroll bars to move through the
colorbar samples.

.. note:: When the plugin starts for the first time, it will generate
        a bitmap RGB image of colorbars and labels corresponding to
        all the available colormaps.  This can take a few seconds
        depending on the number of colormaps installed.

        Colormaps are shown with the "ramp" intensity map applied.

It is customizable using ``~\.ginga\plugin_ColorMapPicker.cfg``, where ``~``
is your HOME directory:

.. code-block:: python
   :linenos:
   
   #
   # ColorMapPicker plugin preferences file
   #
   # Place this in file under ~/.ginga with the name "plugin_ColorMapPicker.cfg"

   cbar_ht = 20
   cbar_wd = 300
   cbar_sep = 10
   cbar_pan_accel = 1.0
