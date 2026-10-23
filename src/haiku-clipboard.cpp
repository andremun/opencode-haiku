// Copyright (c) 2026 Mario Andres Munoz
// Distributed under the terms of the MIT License. See LICENSE.
#include <Application.h>
#include <Clipboard.h>
#include <Message.h>
#include <cstdio>
#include <cstring>
#include <string>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    BApplication app("application/x-vnd.opencode-clipboard");
    BClipboard clipboard("system");
    if (!clipboard.Lock()) return 3;
    status_t status = B_OK;
    if (!strcmp(argv[1], "read")) {
        const void* bytes = nullptr; ssize_t size = 0;
        status = clipboard.Data()->FindData("text/plain", B_MIME_TYPE, &bytes, &size);
        if (status == B_NAME_NOT_FOUND) status = B_OK;
        else if (status == B_OK && size > 0 && fwrite(bytes, 1, size, stdout) != (size_t)size) status = B_ERROR;
    } else if (!strcmp(argv[1], "write")) {
        std::string text; char buffer[8192]; size_t count;
        while ((count = fread(buffer, 1, sizeof(buffer), stdin))) {
            text.append(buffer, count);
            if (text.size() > 8 * 1024 * 1024) { clipboard.Unlock(); return 4; }
        }
        if (ferror(stdin) || text.find('\0') != std::string::npos) status = B_BAD_VALUE;
        else {
            clipboard.Clear();
            status = clipboard.Data()->AddData("text/plain", B_MIME_TYPE, text.data(), text.size());
            if (status == B_OK) status = clipboard.Commit();
        }
    } else if (!strcmp(argv[1], "clear")) {
        clipboard.Clear(); status = clipboard.Commit();
    } else status = B_BAD_VALUE;
    clipboard.Unlock();
    return status == B_OK ? 0 : 1;
}
