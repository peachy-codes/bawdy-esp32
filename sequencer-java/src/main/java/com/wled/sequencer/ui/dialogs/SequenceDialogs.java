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
        String msg = "WLED Sequence Editor [Java Edition]\n" +
                "Version 1.0.0 (Java 17 Swing)\n\n" +
                "Authoring and live orchestration environment for the\n" +
                "headless WLED Lighting Engine over REST API.\n\n" +
                "Key Capabilities:\n" +
                "- Timeline document authoring with dirty-state tracking\n" +
                "- Concurrent multi-layer cue scheduling (Layers 0-9)\n" +
                "- Section organization (Start, Stop, Duration)\n" +
                "- Dynamic pattern and palette discovery\n" +
                "- Continuous interactive scrubbing and time dilation\n" +
                "- Server-side deterministic engine synchronization";
        JOptionPane.showMessageDialog(parent, msg, "About WLED Sequence Editor", JOptionPane.INFORMATION_MESSAGE);
    }
}
