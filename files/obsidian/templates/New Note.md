<%*
let title = tp.file.title
if (title.startsWith("Untitled")) {
  title = await tp.system.prompt("Title");
}
await tp.file.rename(title)
-%>
---
categories: 
  - note
date: <% tp.file.creation_date("YYYY-MM-DD") %>
month: <% tp.file.creation_date("MM") %>
year: <% tp.file.creation_date("YYYY") %>
tags: [y<% tp.file.creation_date("YYYY") %>]
type:  note
title: <% title %>

---


---
> [!createdat] Created at: [[<% tp.date.now("YYYY-MM-DD") %>]]