// Add-on
// Extended frame management
// Rev.2

if (typeof STRING_FRAME_INSERT == "undefined")
  STRING_FRAME_INSERT = "＋ 現ページ複製";
if (typeof STRING_FRAME_DELETE == "undefined")
  STRING_FRAME_DELETE = "－ 現ページ削除";
if (typeof STRING_FRAME_DELPAST == "undefined")
  STRING_FRAME_DELPAST = "／ 前ページまでを削除";
if (typeof STRING_FRAME_IMPORT == "undefined")
  STRING_FRAME_IMPORT = "＃ 追加読み込み";
if (typeof STRING_DELPAST_CONFIRM == "undefined")
  STRING_DELPAST_CONFIRM = "前ページまでを完全に削除してよろしいですか？";

addon_ui += "<hr width=90% size=1>";
addon_ui +=
  '<input type=button value="' +
  STRING_FRAME_DELETE +
  '" onclick="deletepage();dblclickchk=1;" ondblclick="if(dblclickchk==0)deletepage();"><br>';
addon_ui +=
  '<input type=button value="' +
  STRING_FRAME_INSERT +
  '" onclick="insertpage();dblclickchk=1;" ondblclick="if(dblclickchk==0)insertpage();"><br>';
addon_ui +=
  '<input type=button value="' +
  STRING_FRAME_DELPAST +
  '" onclick="delpastpage();"><br>';
addon_ui +=
  '<input type=button value="' +
  STRING_FRAME_IMPORT +
  '" onclick="importpage();"><br>';

function copyframe(srcframe, dstframe) {
  for (var pfi = 0; pfi < fldblks; pfi++)
    af[dstframe * fldblks + pfi] = af[srcframe * fldblks + pfi];
  for (var pfi = 0; pfi < 3; pfi++)
    ap[dstframe * 3 + pfi] = ap[srcframe * 3 + pfi];
  au[dstframe] = au[srcframe];
  am[dstframe] = am[srcframe];
  ac[dstframe] = ac[srcframe];
  ad[dstframe] = ad[srcframe];
}

function insertpage() {
  var dc = document.getElementById("dc");
  if (framemax >= framelim - 1) return;
  pushframe(frame);
  for (var i = framemax; i >= frame; i--) {
    copyframe(i, i + 1);
  }
  framemax++;
  ad[frame] = true;
  frame++;
  popframe(frame);
  updated();
  refreshPage();
  refresh();
}

function deletepage() {
  if (frame >= framemax) return;
  for (var i = frame; i < framemax; i++) {
    copyframe(i + 1, i);
  }
  framemax--;
  popframe(frame);
  updated();
  refreshPage();
  refresh();
}

function delpastpage() {
  if (frame <= 0) return;
  if (confirm(STRING_DELPAST_CONFIRM) != 1) return;
  pushframe(frame);
  for (var i = 0; i <= framemax - frame; i++) {
    copyframe(i + frame, i);
  }
  framemax = framemax - frame;
  frame = 0;
  updated();
  refreshPage();
}

function importpage() {
  if (framemax < framelim - 1) {
    importframemax = framemax;
    importupdateflag = updateflag;
    pgnext(2);
    pgnext(0);
    updateflag = 0;
    versioncheck(frame);
    if (framemax > framelim - 1) framemax = framelim - 1;
    if (importupdateflag || framemax != importframemax) updated();
    refreshPage();
  }
}
