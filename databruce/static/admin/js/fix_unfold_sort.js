document.addEventListener("DOMContentLoaded", () => {
  // Watch for DOM reordering inside inline groups
  const inlineGroups = document.querySelectorAll(".inline-group");

  inlineGroups.forEach((group) => {
    const observer = new MutationObserver(() => {
      const rows = group.querySelectorAll(".inline-related:not(.empty-form)");
      rows.forEach((row, index) => {
        const input = row.querySelector('input[name$="-song_num"]');
        if (input && input.value !== String(index + 1)) {
          input.value = index + 1;
          input.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
    });

    observer.observe(group, { childList: true, subtree: true });
  });
});