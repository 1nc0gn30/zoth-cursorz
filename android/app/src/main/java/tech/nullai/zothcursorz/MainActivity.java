package tech.nullai.zothcursorz;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int OVERLAY_PERMISSION_REQ = 1234;
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        webView.addJavascriptInterface(new WebAppInterface(), "AndroidBridge");
        webView.loadUrl("file:///android_asset/android_dashboard.html");
        setContentView(webView);

        checkOverlayPermission();
    }

    private void checkOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!Settings.canDrawOverlays(this)) {
                Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:" + getPackageName()));
                startActivityForResult(intent, OVERLAY_PERMISSION_REQ);
            }
        }
    }

    public class WebAppInterface {
        @JavascriptInterface
        public void toggleOverlay() {
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(MainActivity.this)) {
                    Toast.makeText(MainActivity.this, "Please grant Overlay Permission first", Toast.LENGTH_LONG).show();
                    checkOverlayPermission();
                    return;
                }
                Intent serviceIntent = new Intent(MainActivity.this, CursorOverlayService.class);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(serviceIntent);
                } else {
                    startService(serviceIntent);
                }
                Toast.makeText(MainActivity.this, "Zoth Multi-Agent Overlay Started", Toast.LENGTH_SHORT).show();
            });
        }

        @JavascriptInterface
        public void openAccessibilitySettings() {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
        }

        @JavascriptInterface
        public void dispatchAgentTap(String agentId) {
            runOnUiThread(() -> {
                Toast.makeText(MainActivity.this, "Autonomous tap executed for " + agentId, Toast.LENGTH_SHORT).show();
            });
        }
    }
}
