require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const schedule = require('node-schedule');
const express = require('express');

// Create Express app for keeping the service alive on Render
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Army Countdown Bot is running!');
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

// Bot configuration
const token = process.env.TELEGRAM_BOT_TOKEN;
let chatId = process.env.CHAT_ID; // Using let instead of const to allow updating
const armyStartDate = new Date(process.env.ARMY_START_DATE);
const armyServiceLengthDays = parseInt(process.env.ARMY_SERVICE_LENGTH_DAYS || '365');

// Calculate discharge date (army start date + service length)
const armyEndDate = new Date(armyStartDate);
armyEndDate.setDate(armyEndDate.getDate() + armyServiceLengthDays);

// Initialize the bot
const bot = new TelegramBot(token, { polling: true });

// Welcome message when bot is added to a chat
bot.on('new_chat_members', (msg) => {
  const newMembers = msg.new_chat_members;
  const botInfo = bot.botInfo;
  
  if (newMembers.some(member => member.id === botInfo.id)) {
    chatId = msg.chat.id; // Update chatId with current chat
    bot.sendMessage(msg.chat.id, 'Привет! Я буду отсчитывать дни до армии, а затем до дембеля.');
    sendCountdownMessage();
  }
});

// Function to calculate days remaining until a specific date
function getDaysRemaining(targetDate) {
  const now = new Date();
  const timeDiff = targetDate.getTime() - now.getTime();
  return Math.ceil(timeDiff / (1000 * 3600 * 24));
}

// Function to send countdown message
function sendCountdownMessage() {
  const now = new Date();
  let message = '';
  
  if (now < armyStartDate) {
    // Before army
    const daysToArmy = getDaysRemaining(armyStartDate);
    message = `Осталось ${daysToArmy} дней до армии`;
  } else {
    // After army started
    const daysToDemobilization = getDaysRemaining(armyEndDate);
    message = `Остался ${daysToDemobilization} дней до дембеля`;
  }
  
  bot.sendMessage(chatId, message)
    .catch(error => console.error('Error sending message:', error));
}

// Schedule daily message at 00:00 UTC+4
// Note: Node-schedule uses server time, so we need to adjust based on server timezone
// UTC+4 is 4 hours ahead of UTC
const rule = new schedule.RecurrenceRule();
rule.hour = 20; // 00:00 UTC+4 is 20:00 UTC
rule.minute = 0;
rule.tz = 'UTC';

// Schedule the job
const job = schedule.scheduleJob(rule, sendCountdownMessage);

// Manual commands for testing
bot.onText(/\/countdown/, (msg) => {
  sendCountdownMessage();
});

// Allow setting chat ID via command
bot.onText(/\/setchat/, (msg) => {
  chatId = msg.chat.id;
  bot.sendMessage(msg.chat.id, `Chat ID установлен: ${chatId}`);
  sendCountdownMessage();
});

// Send initial countdown on startup
if (chatId) {
  sendCountdownMessage();
}

console.log('Army Countdown Bot is running!');

// Keep the bot alive
process.on('SIGINT', () => {
  job.cancel();
  bot.stopPolling();
  process.exit(0);
});

// Handle unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
}); 