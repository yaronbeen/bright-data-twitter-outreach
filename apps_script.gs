/**
 * Twitter/X Outreach Email Sender
 *
 * HOW TO USE:
 * 1. Open your Google Sheet with the outreach data
 * 2. Go to Extensions > Apps Script
 * 3. Delete everything in the editor and paste this entire script
 * 4. Click Save (floppy disk icon)
 * 5. Go back to your spreadsheet - you'll see a new "Outreach" menu
 * 6. Use Outreach > Send All Pending Emails to start sending
 *
 * SHEET FORMAT (columns A-F):
 *   A: profile_name
 *   B: email
 *   C: followers
 *   D: subject
 *   E: body
 *   F: status (leave empty - script fills this in)
 *
 * Row 1 = headers. Data starts at row 2.
 */

// ── CONFIG ──────────────────────────────────────────────────
const SENDER_NAME = "Yaron Been";
const DELAY_SECONDS = 45;
const SHEET_NAME = "Sheet1";
const STATUS_COL = 6;
const DRY_RUN = false;
// ─────────────────────────────────────────────────────────────

function onOpen() {
  SpreadsheetApp.getUi().createMenu("Outreach")
    .addItem("Send All Pending Emails", "sendAllEmails")
    .addItem("Send Next 5 Emails", "sendNext5")
    .addItem("Send Test Email to Myself", "sendTestEmail")
    .addSeparator()
    .addItem("Reset All Statuses", "resetStatuses")
    .addItem("Check Gmail Daily Quota", "checkQuota")
    .addToUi();
}

function sendAllEmails() { sendEmails(999); }
function sendNext5() { sendEmails(5); }

function sendEmails(maxToSend) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet '" + SHEET_NAME + "' not found.");
    return;
  }

  var data = sheet.getDataRange().getValues();
  var sentCount = 0, errorCount = 0, skippedCount = 0;

  for (var i = 1; i < data.length && sentCount < maxToSend; i++) {
    var row = data[i];
    var profileName = row[0], email = row[1], followers = row[2];
    var subject = row[3], body = row[4], status = row[5];

    if (status && status.toString().trim() !== "") { skippedCount++; continue; }
    if (!email || email.toString().trim() === "") { sheet.getRange(i+1, STATUS_COL).setValue("NO EMAIL"); skippedCount++; continue; }
    if (!body || body.toString().trim() === "") { sheet.getRange(i+1, STATUS_COL).setValue("NO BODY"); skippedCount++; continue; }

    try {
      var htmlBody = body.toString()
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>").replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');

      if (DRY_RUN) {
        Logger.log("DRY RUN - Would send to: " + email);
        sheet.getRange(i+1, STATUS_COL).setValue("DRY RUN - " + new Date().toLocaleDateString());
      } else {
        GmailApp.sendEmail(email.toString().trim(), subject, body, { name: SENDER_NAME, htmlBody: htmlBody });
        sheet.getRange(i+1, STATUS_COL).setValue("SENT - " + new Date().toLocaleDateString());
        Logger.log("Sent to: " + profileName + " (" + email + ")");
      }

      sentCount++;
      if (sentCount < maxToSend && i < data.length - 1) Utilities.sleep(DELAY_SECONDS * 1000);
    } catch (e) {
      sheet.getRange(i+1, STATUS_COL).setValue("ERROR: " + e.message);
      Logger.log("Error sending to " + email + ": " + e.message);
      errorCount++;
    }
  }

  SpreadsheetApp.getUi().alert("Done!\n\nSent: " + sentCount + "\nErrors: " + errorCount + "\nSkipped: " + skippedCount);
}

function sendTestEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) { SpreadsheetApp.getUi().alert("No data found."); return; }

  var row = data[1];
  var subject = "[TEST] " + row[3], body = row[4];
  var myEmail = Session.getActiveUser().getEmail();

  var htmlBody = body.toString()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>").replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');

  GmailApp.sendEmail(myEmail, subject, body, { name: SENDER_NAME, htmlBody: htmlBody });
  SpreadsheetApp.getUi().alert("Test email sent to " + myEmail);
}

function resetStatuses() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.alert("Reset All Statuses",
    "This will clear all status values, allowing emails to be sent again.\n\nAre you sure?",
    ui.ButtonSet.YES_NO);
  if (response !== ui.Button.YES) return;

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var lastRow = sheet.getLastRow();
  if (lastRow > 1) { sheet.getRange(2, STATUS_COL, lastRow - 1, 1).clearContent(); ui.alert("All statuses cleared."); }
}

function checkQuota() {
  var remaining = MailApp.getRemainingDailyQuota();
  SpreadsheetApp.getUi().alert("Gmail Daily Quota\n\nEmails remaining today: " + remaining +
    "\n\nFree Gmail: 100/day\nGoogle Workspace: 1,500/day");
}
