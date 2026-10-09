package com.wled.sequencer.ui.dialogs;

import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceRepository;
import com.wled.sequencer.model.SequenceSummary;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.List;

/**
 * Open, Save As, and About modal dialogs using default Swing settings.
 */
public class SequenceDialogs {

    public record SelectedSequence(String filename, SequenceData data) {}

    public static SelectedSequence showOpenSequenceDialog(Component parent, SequenceRepository repo) {
        List<SequenceSummary> list = repo.listSequences();
        if (list.isEmpty()) {
            JOptionPane.showMessageDialog(parent, "No sequence files found in " + repo.getDirectory(),
                    "Open Sequence", JOptionPane.INFORMATION_MESSAGE);
            return null;
        }

        String[] cols = {"Filename", "Sequence Name", "Cues", "Duration"};
        Object[][] data = new Object[list.size()][4];
        for (int i = 0; i < list.size(); i++) {
            SequenceSummary s = list.get(i);
            data[i][0] = s.filename();
            data[i][1] = s.name();
            data[i][2] = s.stepCount();
            data[i][3] = String.format("%.1fs", s.totalDuration());
        }

        JTable table = new JTable(new DefaultTableModel(data, cols) {
            @Override
            public boolean isCellEditable(int r, int c) { return false; }
        });
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setRowHeight(22);
        table.setRowSelectionInterval(0, 0);

        JScrollPane scroll = new JScrollPane(table);
        scroll.setPreferredSize(new Dimension(520, 220));
        scroll.setBorder(BorderFactory.createLineBorder(new Color(210, 210, 210), 1));

        int res = JOptionPane.showConfirmDialog(parent, scroll, "Open Sequence File",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (res == JOptionPane.OK_OPTION && table.getSelectedRow() != -1) {
            String fname = (String) table.getValueAt(table.getSelectedRow(), 0);
            SequenceData seq = repo.loadSequence(fname);
            return new SelectedSequence(fname, seq);
        }
        return null;
    }

    public static SequenceData showOpenDialog(Component parent, SequenceRepository repo) {
        SelectedSequence sel = showOpenSequenceDialog(parent, repo);
        return sel != null ? sel.data() : null;
    }

    public static String showNewSequenceDialog(Component parent) {
        JPanel p = new JPanel(new GridLayout(2, 1, 4, 4));
        p.add(new JLabel("New Show / Sequence Name:"));
        JTextField txt = new JTextField("Metro Concert Opening Show", 22);
        txt.selectAll();
        p.add(txt);

        int res = JOptionPane.showConfirmDialog(parent, p, "Create New Show Sequence",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (res == JOptionPane.OK_OPTION) {
            String val = txt.getText().trim();
            return val.isBlank() ? "Untitled Sequence" : val;
        }
        return null;
    }

    public static String showSaveAsDialog(Component parent, String currentName) {
        JPanel p = new JPanel(new GridLayout(2, 1, 4, 4));
        p.add(new JLabel("Enter Sequence / File Name:"));
        JTextField txt = new JTextField(currentName != null ? currentName : "My Lighting Show", 20);
        p.add(txt);

        int res = JOptionPane.showConfirmDialog(parent, p, "Save Sequence As",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (res == JOptionPane.OK_OPTION) {
            String val = txt.getText().trim();
            return val.isBlank() ? null : val;
        }
        return null;
    }

    public static void showAboutDialog(Component parent) {
        String msg = "WLED Universe Manager [Java Desktop Edition]\n" +
                "Version 2.0.0 (Java 17 Swing)\n\n" +
                "Multi-Node Lighting Orchestrator & Spatial Digital Twin Studio\n" +
                "Coordinates 20+ hardwired Cat6 WLED controllers, 5,153+ LEDs, and\n" +
                "venue spatial arrangement over high-speed DDP UDP sync.\n\n" +
                "Core Architecture:\n" +
                "• Universe Management: 28 fixtures across 9 physical venue zones\n" +
                "• Cat6 Controller Fleet: 20 WLED ESP32 nodes (ports 4048-4067)\n" +
                "• Hardware Sync: DDP 0x41 broadcast sync with sub-millisecond drift\n" +
                "• Spatial Sampling: Continuous 3D parametric coordinate mapping\n" +
                "• Multi-Layer Timeline: 10 concurrent compositing engine layers\n" +
                "• Performance: Optimized 30 FPS zero-allocation Swing pipeline";
        JOptionPane.showMessageDialog(parent, msg, "About WLED Universe Manager", JOptionPane.INFORMATION_MESSAGE);
    }

    public static void showArchitectureGuideDialog(Component parent) {
        String guide = "=== WLED Multi-Node Universe Architecture ===\n\n" +
                "1. Tier 1: 20-Node ESP32 Virtual Hardware Simulator\n" +
                "   • 20 UDP endpoints listening on 0.0.0.0:4048..4067\n" +
                "   • Hardware integrity engine and telemetry\n" +
                "   • Browser visualizer at http://localhost:8080\n\n" +
                "2. Tier 2: Python Lighting Engine REST Daemon\n" +
                "   • High-precision monotonic frame clock (30 FPS)\n" +
                "   • Continuous 3D spatial field sampling\n" +
                "   • Patch routing across Cat6 switch\n" +
                "   • REST JSON API on http://127.0.0.1:8765\n\n" +
                "3. Tier 3: WLED Universe Manager (Java Desktop Edition)\n" +
                "   • Venue blueprint & 28-fixture spatial canvas\n" +
                "   • Controller fleet & hardware patch editor\n" +
                "   • Multi-layer timeline sequence authoring\n" +
                "   • Real-time atomic blackout & 0x41 DDP broadcast sync";
        JOptionPane.showMessageDialog(parent, guide, "WLED Architecture & Protocol Guide", JOptionPane.INFORMATION_MESSAGE);
    }
}
