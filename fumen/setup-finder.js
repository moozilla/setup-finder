// Add-on
// Fumen add-on for importing setup-finder output.txt into a single diagram
// Rev.1

if (typeof STRING_SETUP_FINDER == "undefined")
  STRING_SETUP_FINDER = "% Import setup";

addon_ui +=
  '<input type=button value="' +
  STRING_SETUP_FINDER +
  '" onclick="importsetup();"><br>';

function importsetup() {
  setups = tx.value.split("\n");
  tx.value = setups[0].split(" ")[1];
  versioncheck(0); //inital frame import
  for (var i = 2; i < setups.length; i++) {
    fsplit = setups[i].split(" (");
    tx.value = fsplit[0];
    importpage();
    cm.value = fsplit[1].slice(0, -1);
  }
}
