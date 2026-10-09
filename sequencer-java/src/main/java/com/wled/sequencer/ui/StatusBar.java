package com.wled.sequencer.ui;

import javax.swing.*;
import java.awt.*;

/**
 * Segmented status bar displaying document state, cues, timeline duration, and engine FPS.
 */
public class StatusBar extends JPanel {
    private final JLabel lblDocStatus = new JLabel("Document: Saved");
    private final JLabel lblStatus = new JLabel("Ready");
    private final JLabel lblCues = new JLabel("Cues: 0");
    private final JLabel lblTotalTime = new JLabel("Total: 0.0s");
    private final JLabel lblFps = new JLabel("Engine: -- FPS");

    public StatusBar() {
        setLayout(new GridBagLayout());
        setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(1, 0, 0, 0, new Color(215, 215, 215)),
                BorderFactory.createEmptyBorder(2, 4, 2, 4)
        ));

        GridBagConstraints g = new GridBagConstraints();
        g.fill = GridBagConstraints.BOTH;
        g.insets = new Insets(1, 2, 1, 2);

        // Panel 0: Document Saved/Dirty State
        g.gridx = 0;
        g.weightx = 0.0;
        lblDocStatus.setPreferredSize(new Dimension(135, 20));
        lblDocStatus.setForeground(new Color(40, 140, 50));
        add(createSegment(lblDocStatus), g);

        // Panel 1: Status message (expands to fill space)
        g.gridx = 1;
        g.weightx = 1.0;
        add(createSegment(lblStatus), g);

        // Panel 2: Cues count
        g.gridx = 2;
        g.weightx = 0.0;
        lblCues.setPreferredSize(new Dimension(80, 20));
        add(createSegment(lblCues), g);

        // Panel 3: Total duration
        g.gridx = 3;
        g.weightx = 0.0;
        lblTotalTime.setPreferredSize(new Dimension(95, 20));
        add(createSegment(lblTotalTime), g);

        // Panel 4: Engine FPS
        g.gridx = 4;
        lblFps.setPreferredSize(new Dimension(110, 20));
        add(createSegment(lblFps), g);
    }

    private JPanel createSegment(JLabel label) {
        JPanel p = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 1));
        p.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
                BorderFactory.createEmptyBorder(1, 4, 1, 4)
        ));
        p.add(label);
        return p;
    }

    public void setDocumentDirty(boolean dirty) {
        if (dirty) {
            lblDocStatus.setText("Document: Modified *");
            lblDocStatus.setForeground(new Color(180, 70, 0));
        } else {
            lblDocStatus.setText("Document: Saved");
            lblDocStatus.setForeground(new Color(40, 140, 50));
        }
    }

    public void setStatus(String status) {
        lblStatus.setText(status);
    }

    public void setCueCount(int count) {
        lblCues.setText("Cues: " + count);
    }

    public void setTotalDuration(double seconds) {
        lblTotalTime.setText(String.format("Total: %.1fs", seconds));
    }

    public void setFps(double fps) {
        lblFps.setText(String.format("Engine: %.1f FPS", fps));
    }
}
