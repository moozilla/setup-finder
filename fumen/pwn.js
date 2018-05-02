//pwn's fumen modifications - change key inputs for quiz, and removes warning from clear to end
delpage = function() {
  var pg = document.getElementById("pg");
  var dc = document.getElementById("dc");
  if (frame < framemax) {
    framemax = frame;
    updated();
    refreshPage();
    dc.checked = false;
  }
};
keyevent = function() {
  var kbd = document.getElementById("kbd");
  kbdval = kbd.value;
  while (!kbd.disabled && kbdval.length > 0) {
    kbdchr = kbdval.substring(0, 1);
    if ("Kk".indexOf(kbdchr) >= 0) kmove(-1);
    if ("Ll".indexOf(kbdchr) >= 0) kdrop(1);
    if ("Oo".indexOf(kbdchr) >= 0) kdrop(-1);
    if (";:".indexOf(kbdchr) >= 0) kmove(1);
    if ("Aa".indexOf(kbdchr) >= 0) krot(1);
    if ("Ss".indexOf(kbdchr) >= 0) krot(-1);
    if ("Dd".indexOf(kbdchr) >= 0) khold();
    if ("Rr".indexOf(kbdchr) >= 0) pgprev(0);
    if ("Tt".indexOf(kbdchr) >= 0) pgnext(0);
    if ("Ee".indexOf(kbdchr) >= 0) delpage();
    kbdval = kbdval.substring(1);
  }
  kbd.value = kbdval;
};
