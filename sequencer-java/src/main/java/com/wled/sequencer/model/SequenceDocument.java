package com.wled.sequencer.model;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Encapsulates the authoring document state, file path, and dirty/saved tracking
 * for the WLED Sequence Editor.
 */
public class SequenceDocument {

    public interface DocumentListener {
        void onDocumentStateChanged(SequenceDocument doc);
    }

    private SequenceData data;
    private String filename;
    private boolean dirty = false;
    private final List<DocumentListener> listeners = new CopyOnWriteArrayList<>();

    public SequenceDocument(SequenceData data, String filename) {
        this.data = data != null ? data : new SequenceData("Untitled Sequence");
        this.filename = filename;
        this.dirty = false;
    }

    public SequenceDocument() {
        this(new SequenceData("Untitled Sequence"), null);
    }

    public SequenceData getData() {
        return data;
    }

    public void setData(SequenceData data, String filename) {
        this.data = data != null ? data : new SequenceData("Untitled Sequence");
        this.filename = filename;
        this.dirty = false;
        notifyListeners();
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
        notifyListeners();
    }

    public String getTitle() {
        String base = filename != null && !filename.isBlank() ? filename : data.getName();
        if (base == null || base.isBlank()) base = "Untitled";
        return dirty ? base + " *" : base;
    }

    public boolean isDirty() {
        return dirty;
    }

    public void markDirty() {
        if (!this.dirty) {
            this.dirty = true;
            notifyListeners();
        }
    }

    public void markClean() {
        if (this.dirty) {
            this.dirty = false;
            notifyListeners();
        }
    }

    public void addListener(DocumentListener listener) {
        listeners.add(listener);
    }

    public void removeListener(DocumentListener listener) {
        listeners.remove(listener);
    }

    private void notifyListeners() {
        for (DocumentListener l : listeners) {
            l.onDocumentStateChanged(this);
        }
    }
}
