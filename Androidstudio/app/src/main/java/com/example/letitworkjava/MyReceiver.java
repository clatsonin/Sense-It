package com.example.letitworkjava;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.telephony.SmsMessage;
import android.widget.Toast;

public class MyReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent != null && intent.getAction() != null && intent.getAction().equals("android.provider.Telephony.SMS_RECEIVED")) {
            SmsMessage smsMessage = extractMessage(context, intent);

            if (smsMessage != null) {
                String senderPhoneNumber = smsMessage.getOriginatingAddress();
                String receivedMessage = smsMessage.getMessageBody();
                // Display received message and sender's phone number in a Toast
                String toastMessage = "Received Message: " + receivedMessage + "\nFrom: " + senderPhoneNumber;
                Toast.makeText(context, toastMessage, Toast.LENGTH_SHORT).show();

                // Send a broadcast to update the TextView in MainActivity
                Intent updateIntent = new Intent("UPDATE_TEXTVIEW");
                updateIntent.putExtra("message", receivedMessage);
                updateIntent.putExtra("sender", senderPhoneNumber);
                context.sendBroadcast(updateIntent);
            }
        }
    }

    private SmsMessage extractMessage(Context context, Intent intent) {
        SmsMessage[] messages;
        try {
            Object[] pdus = (Object[]) intent.getExtras().get("pdus");
            if (pdus != null) {
                messages = new SmsMessage[pdus.length];
                for (int i = 0; i < messages.length; i++) {
                    messages[i] = SmsMessage.createFromPdu((byte[]) pdus[i]);
                }
                return messages[0];
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
