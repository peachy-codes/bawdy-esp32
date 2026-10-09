package com.wled.sequencer.ui.transport;

import com.wled.sequencer.client.EngineClient;
import com.wled.sequencer.player.PlayerListener;
import com.wled.sequencer.player.TimelinePlayer;

import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Set;

/**
 * Transport controls, timeline progress scrubber, loop settings, and daemon telemetry HUD.
 * Uses default Swing settings and Arial font throughout.
 */
public class TransportPanel extends JPanel {
    private final TimelinePlayer player;
    private final EngineClient engineClient;

    // Transport buttons
    private final JButton btnPlay = new JButton("Play");
    private final JButton btnPause = new JButton("Pause");
    private final JButton btnStop = new JButton("Stop");
    private final JButton btnPrev = new JButton("Prev");
    private final JButton btnNext = new JButton("Next");

    // Monospace digital readout
    private final JLabel lblTimeDisplay = new JLabel("TIME: 00:00.0 / 00:00.0 | ACTIVE: 0 Cues");

    // Looping
    private final JComboBox<String> cmbLoopMode = new JComboBox<>(new String[]{
            "Loop Infinitely", "Play N Times", "Play Once & Hold", "Play Once & Blackout"
    });
    private final JSpinner spnLoopCount = new JSpinner(new SpinnerNumberModel(1, 1, 999, 1));

    // Timeline Scrubber
    private final JSlider sldTimeline = new JSlider(0, 1000, 0);

    // Global Speed
    private final JSlider sldDilation = new JSlider(1, 40, 10);
    private final JLabel lblDilationVal = new JLabel("1.0x");

    // Daemon status
    private final JTextField txtDaemonUrl = new JTextField("http://127.0.0.1:8765", 14);
    private final JButton btnPing = new JButton("Ping");
    private final JLabel lblDaemonStatus = new JLabel("[Checking...]");

    public TransportPanel(TimelinePlayer player, EngineClient engineClient) {
        this.player = player;
        this.engineClient = engineClient;

        setLayout(new BorderLayout(4, 4));
        setBorder(BorderFactory.createTitledBorder("Playback & Transport Controls"));

        // --- ROW 1: Controls, Digital Readout, Loop Settings ---
        JPanel topRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 2));

        JButton[] transportBtns = {btnPlay, btnPause, btnStop, btnPrev, btnNext};
        for (JButton b : transportBtns) {
            topRow.add(b);
        }

        // Digital display
        lblTimeDisplay.setFont(new Font("Arial", Font.BOLD, 12));
        lblTimeDisplay.setPreferredSize(new Dimension(360, 26));
        lblTimeDisplay.setHorizontalAlignment(SwingConstants.CENTER);
        lblTimeDisplay.setBorder(BorderFactory.createLineBorder(new Color(200, 200, 200), 1));
        topRow.add(lblTimeDisplay);

        // Looping
        topRow.add(new JLabel("Looping:"));
        topRow.add(cmbLoopMode);
        spnLoopCount.setPreferredSize(new Dimension(48, 24));
        spnLoopCount.setVisible(false);
        topRow.add(spnLoopCount);

        // --- ROW 2: Interactive Scrubber Slider ---
        JPanel midRow = new JPanel(new BorderLayout(4, 2));
        midRow.setBorder(BorderFactory.createEmptyBorder(2, 4, 2, 4));
        sldTimeline.setFocusable(false);
        midRow.add(sldTimeline, BorderLayout.CENTER);

        // --- ROW 3: Time Dilation & Engine Connection ---
        JPanel bottomRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 2));

        bottomRow.add(new JLabel("Speed:"));
        sldDilation.setPreferredSize(new Dimension(100, 22));
        bottomRow.add(sldDilation);
        lblDilationVal.setFont(new Font("Arial", Font.PLAIN, 12));
        lblDilationVal.setPreferredSize(new Dimension(35, 20));
        bottomRow.add(lblDilationVal);

        bottomRow.add(Box.createHorizontalStrut(15));
        bottomRow.add(new JLabel("Engine Daemon:"));
        bottomRow.add(txtDaemonUrl);
        bottomRow.add(btnPing);

        lblDaemonStatus.setFont(new Font("Arial", Font.BOLD, 12));
        lblDaemonStatus.setForeground(Color.GRAY);
        bottomRow.add(lblDaemonStatus);

        // Assemble panels
        JPanel centerContainer = new JPanel();
        centerContainer.setLayout(new BoxLayout(centerContainer, BoxLayout.Y_AXIS));
        centerContainer.add(topRow);
        centerContainer.add(midRow);
        centerContainer.add(bottomRow);

        add(centerContainer, BorderLayout.CENTER);

        setupEventBindings();
        checkEngineHealth();
        setupHeartbeatTimer();
    }

    private void setupEventBindings() {
        // Transport actions
        btnPlay.addActionListener(e -> player.play());
        btnPause.addActionListener(e -> player.pause());
        btnStop.addActionListener(e -> player.stop());
        btnPrev.addActionListener(e -> player.seek(0.0));
        btnNext.addActionListener(e -> player.seek(player.getSequence().getTotalDuration()));

        // Scrubber dragging and clicking
        sldTimeline.addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
                seekByMousePosition(e.getX());
            }
        });

        sldTimeline.addMouseMotionListener(new MouseAdapter() {
            @Override
            public void mouseDragged(MouseEvent e) {
                seekByMousePosition(e.getX());
            }
        });

        // Speed slider
        sldDilation.addChangeListener(e -> {
            double dilation = sldDilation.getValue() / 10.0;
            lblDilationVal.setText(String.format("%.1fx", dilation));
            player.getSequence().setTimeDilation(dilation);
        });

        // Loop mode
        cmbLoopMode.addActionListener(e -> {
            int idx = cmbLoopMode.getSelectedIndex();
            spnLoopCount.setVisible(idx == 1);
            String modeStr = switch (idx) {
                case 1 -> "count";
                case 2 -> "once";
                case 3 -> "blackout";
                default -> "infinite";
            };
            player.getSequence().setLoopMode(modeStr);
            revalidate();
            repaint();
        });

        spnLoopCount.addChangeListener(e -> {
            player.getSequence().setLoopCount((Integer) spnLoopCount.getValue());
        });

        // Daemon Ping
        btnPing.addActionListener(e -> {
            if (engineClient != null) {
                engineClient.setBaseUrl(txtDaemonUrl.getText().trim());
                checkEngineHealth();
            }
        });

        // Connect player listener to update HUD
        player.addListener(new PlayerListener() {
            @Override
            public void onPlaybackTick(double elapsedSec, double totalDurationSec, int activeCount) {
                SwingUtilities.invokeLater(() -> {
                    updateTimeDisplay(elapsedSec, totalDurationSec, activeCount);
                    if (!sldTimeline.getValueIsAdjusting() && totalDurationSec > 0) {
                        int pos = (int) ((elapsedSec / totalDurationSec) * 1000);
                        sldTimeline.setValue(Math.min(1000, Math.max(0, pos)));
                    }
                });
            }

            @Override
            public void onActiveCuesChanged(Set<String> activeCueIds) {
                SwingUtilities.invokeLater(() -> {
                    updateTimeDisplay(player.getTotalElapsedSec(), player.getSequence().getTotalDuration(), activeCueIds.size());
                });
            }

            @Override
            public void onPlaybackStateChanged(boolean isPlaying, boolean isPaused) {
                SwingUtilities.invokeLater(() -> {
                    updateTransportButtons(isPlaying, isPaused);
                });
            }
        });

        updateTransportButtons(player.isPlaying(), player.isPaused());
    }

    private void updateTimeDisplay(double elapsed, double total, int activeCues) {
        int eMin = (int) (elapsed / 60);
        double eSec = elapsed % 60;
        int tMin = (int) (total / 60);
        double tSec = total % 60;

        lblTimeDisplay.setText(String.format("TIME: %02d:%04.1f / %02d:%04.1f | ACTIVE: %d Cues",
                eMin, eSec, tMin, tSec, activeCues));
    }

    private void seekByMousePosition(int mouseX) {
        int width = sldTimeline.getWidth();
        if (width > 0) {
            double ratio = Math.max(0.0, Math.min(1.0, (double) mouseX / width));
            double targetTime = ratio * player.getSequence().getTotalDuration();
            player.seek(targetTime);
        }
    }

    private void updateTransportButtons(boolean isPlaying, boolean isPaused) {
        btnPlay.setEnabled(!isPlaying || isPaused);
        btnPause.setEnabled(isPlaying && !isPaused);
        btnStop.setEnabled(isPlaying || isPaused);
    }

    private java.util.function.Consumer<Double> onFpsUpdatedListener = null;

    public void setOnFpsUpdatedListener(java.util.function.Consumer<Double> listener) {
        this.onFpsUpdatedListener = listener;
    }

    private void checkEngineHealth() {
        if (engineClient == null) return;

        engineClient.ping().thenAccept(status -> SwingUtilities.invokeLater(() -> {
            if (status.isRunning() || "ok".equalsIgnoreCase(status.getStatus())) {
                double fps = status.getActualFps();
                lblDaemonStatus.setText(String.format("[Online (%.1f FPS)]", fps));
                lblDaemonStatus.setForeground(new Color(25, 135, 45));
                if (onFpsUpdatedListener != null) {
                    onFpsUpdatedListener.accept(fps);
                }
            } else {
                lblDaemonStatus.setText("[Offline]");
                lblDaemonStatus.setForeground(new Color(200, 30, 30));
                if (onFpsUpdatedListener != null) {
                    onFpsUpdatedListener.accept(0.0);
                }
            }
        }));
    }

    private void setupHeartbeatTimer() {
        javax.swing.Timer timer = new javax.swing.Timer(2000, e -> checkEngineHealth());
        timer.setRepeats(true);
        timer.start();
    }
}
