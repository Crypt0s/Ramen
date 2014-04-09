<map version="0.9.0">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node CREATED="1368300463190" ID="ID_1375540396" MODIFIED="1368300846691" TEXT="Python 3 support&#xa;in ftputil">
<icon BUILTIN="gohome"/>
<node CREATED="1368300515250" ID="ID_734934983" MODIFIED="1368301855710" POSITION="right" TEXT="Present">
<icon BUILTIN="stop"/>
<node CREATED="1368300520873" ID="ID_1663946434" MODIFIED="1368300527457" TEXT="Only Python 2 supported"/>
<node CREATED="1368300540041" ID="ID_13351353" MODIFIED="1368300749402" TEXT="specifically: Python 2.4 and up"/>
<node CREATED="1368300572520" ID="ID_594539032" MODIFIED="1368300830644" TEXT="API follows semantics &quot;normal&quot; for Python 2">
<node CREATED="1368300586600" ID="ID_1055944287" MODIFIED="1368300600502" TEXT="Methods accept byte strings"/>
<node CREATED="1368300601247" ID="ID_1208559468" MODIFIED="1368300832732" TEXT="They usually also accept unicode strings">
<node CREATED="1368300615407" ID="ID_916370659" MODIFIED="1368300806010" TEXT="Unicode strings are converted to byte strings ..."/>
<node CREATED="1368300626711" ID="ID_613059682" MODIFIED="1368300810762" TEXT="... possibly giving an exception if the strings aren&apos;t purely ASCII"/>
</node>
</node>
</node>
<node CREATED="1368300848386" ID="ID_854838005" MODIFIED="1368301817703" POSITION="right" TEXT="Future">
<icon BUILTIN="go"/>
<node CREATED="1368300854202" ID="ID_288912346" MODIFIED="1368300868360" TEXT="Python 2 is only supported for Python 2.6 and up"/>
<node CREATED="1368300887169" ID="ID_227568724" MODIFIED="1368301803697" TEXT="So supporting Python 2 and 3 with the same code base is much easier"/>
<node CREATED="1368300927488" ID="ID_1507075349" MODIFIED="1368300941807" TEXT="API follows semantics &quot;normal&quot; for Python 3">
<node CREATED="1368301624442" FOLDED="true" ID="ID_1238230082" MODIFIED="1368301788326" TEXT="Python 3 is the future of Python. Python 2 will be &quot;legacy&quot; in the long run.">
<icon BUILTIN="password"/>
<node CREATED="1368301746639" ID="ID_1617489376" MODIFIED="1368301771494" TEXT="So rather have a &quot;Python-3-like&quot; API than a &quot;Python-2-like&quot; API"/>
</node>
<node CREATED="1368300947824" ID="ID_1131977673" MODIFIED="1368300967206" TEXT="Methods usually take unicode strings for file paths"/>
<node CREATED="1368300972783" ID="ID_1854387475" MODIFIED="1368300986606" TEXT="Byte strings are allowed as well"/>
<node CREATED="1368301032326" ID="ID_1494210839" MODIFIED="1368301665124" TEXT="For methods which take and return a string,&#xa;they return the same type they received">
<node CREATED="1368301087245" ID="ID_1007001075" MODIFIED="1368303223349" TEXT="Examples: `os.path.abspath`, `os.listdir`"/>
</node>
</node>
</node>
<node CREATED="1368301162747" ID="ID_813149318" MODIFIED="1368301171404" POSITION="right" TEXT="Watch out">
<icon BUILTIN="messagebox_warning"/>
<node CREATED="1368301173203" ID="ID_1708087311" MODIFIED="1368301248240" TEXT="ftplib in Python 3 uses latin1 for encoding/decoding file names ...">
<node CREATED="1368301198315" ID="ID_1212496193" MODIFIED="1368301477942" TEXT="... whereas for local file names the decoding&#xa;comes from `sys.getfilesystemencoding()`."/>
</node>
<node CREATED="1368301319080" ID="ID_1990387473" MODIFIED="1368301711545" TEXT="Supporting different APIs - i. e. doing things &quot;normally&quot; - for different&#xa;Python versions would make implementation very messy and error-prone.">
<icon BUILTIN="clanbomber"/>
<node CREATED="1368301442789" ID="ID_1761491987" MODIFIED="1368301453204" TEXT="... including the unit tests."/>
<node CREATED="1368301503340" ID="ID_299470919" MODIFIED="1368301976163" TEXT="If someone _really_ wants an API compatible with ftputil 2.8,&#xa;they should implement an adapter layer, possibly with&#xa;corresponding unit tests."/>
</node>
</node>
</node>
</map>
