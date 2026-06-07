import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() => runApp(MaterialApp(
  debugShowCheckedModeBanner: false,
  theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.deepPurple),
  home: const Home(),
));

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  Map<String, List<String>> album = {};
  Set<String> selected = {};
  bool isSelection = false;
  bool isLoading = false;
  String searchQuery = "";
  final String baseUrl = "http://10.0.2.2:8000";

  @override
  void initState() {
    super.initState();
    _load();
  }

  // 修改后的搜索逻辑
  Map<String, List<String>> get filteredAlbum {
    if (searchQuery.isEmpty) return album;

    Map<String, List<String>> result = {};
    String query = searchQuery.toLowerCase();

    album.forEach((category, images) {
      // 逻辑：如果分类名匹配，或者分类下有图片名匹配
      bool categoryMatches = category.toLowerCase().contains(query);

      if (categoryMatches) {
        // 如果分类名匹配，显示该分类下所有图片
        result[category] = images;
      } else {
        // 否则，只过滤出包含搜索词的图片
        final filteredImages = images.where((img) => img.toLowerCase().contains(query)).toList();
        if (filteredImages.isNotEmpty) {
          result[category] = filteredImages;
        }
      }
    });
    return result;
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    final String? j = p.getString('album');
    if (j != null) {
      try {
        final Map<String, dynamic> decoded = jsonDecode(j);
        setState(() {
          album = decoded.map((k, v) => MapEntry(k, List<String>.from(v as List)));
        });
      } catch (e) { debugPrint("Load error: $e"); }
    }
  }

  Future<void> _saveAlbum() async {
    final p = await SharedPreferences.getInstance();
    await p.setString('album', jsonEncode(album));
  }

  Future<void> _delete() async {
    setState(() => isLoading = true);
    for (var i in selected) {
      try { await http.delete(Uri.parse("$baseUrl/delete?filepath=$i")); } catch (_) {}
    }
    setState(() {
      for (var i in selected) album.forEach((k, v) => v.remove(i));
      album.removeWhere((k, v) => v.isEmpty);
      selected.clear();
      isSelection = false;
      isLoading = false;
    });
    await _saveAlbum();
  }

  Future<void> _pick() async {
    final r = await FilePicker.platform.pickFiles(allowMultiple: true, type: FileType.image);
    if (r == null || r.files.isEmpty) return;

    setState(() => isLoading = true);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("사진을 AI로 분석 중입니다...")));

    try {
      var req = http.MultipartRequest("POST", Uri.parse("$baseUrl/upload"));
      for (var f in r.files) {
        if (f.path != null) req.files.add(await http.MultipartFile.fromPath("files", f.path!));
      }
      final res = await req.send().timeout(const Duration(seconds: 60));

      if (res.statusCode == 200) {
        final d = jsonDecode(await res.stream.bytesToString());
        setState(() {
          for (var i in d["images"]) {
            if (!(album[i["category"]]?.contains(i["filename"]) ?? false)) {
              album.putIfAbsent(i["category"], () => []).add(i["filename"]);
            }
          }
        });
        await _saveAlbum();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("업로드 실패: 네트워크를 확인해주세요")));
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayAlbum = filteredAlbum;
    return Scaffold(
      appBar: AppBar(
        title: Text(isSelection ? "${selected.length}개 선택됨" : "AI 스마트 앨범"),
        actions: isSelection ? [
          IconButton(icon: const Icon(Icons.delete_outline), onPressed: _delete),
          IconButton(icon: const Icon(Icons.close), onPressed: () => setState(() {isSelection = false; selected.clear();}))
        ] : null,
      ),
      body: Column(children: [
        Padding(padding: const EdgeInsets.all(16.0), child: TextField(
          decoration: InputDecoration(
            labelText: "검색 (카테고리 또는 사진명)",
            prefixIcon: const Icon(Icons.search),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          ),
          onChanged: (v) => setState(() => searchQuery = v),
        )),
        Expanded(child: isLoading ? const Center(child: CircularProgressIndicator()) : ListView.builder(
            itemCount: displayAlbum.keys.length,
            itemBuilder: (context, index) {
              String key = displayAlbum.keys.elementAt(index);
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Padding(padding: const EdgeInsets.only(left: 16, bottom: 8, top: 8), child: Text(key, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18))),
                SizedBox(height: 120, child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: displayAlbum[key]!.length,
                    itemBuilder: (_, i) {
                      final img = displayAlbum[key]![i];
                      final isS = selected.contains(img);
                      return GestureDetector(
                        onLongPress: () => setState(() => isSelection = true),
                        onTap: () => isSelection ? setState(() => isS ? selected.remove(img) : selected.add(img)) : null,
                        child: Container(
                          margin: const EdgeInsets.only(left: 16),
                          decoration: BoxDecoration(border: isS ? Border.all(color: Colors.deepPurple, width: 4) : null, borderRadius: BorderRadius.circular(8)),
                          child: ClipRRect(borderRadius: BorderRadius.circular(6), child: Image.network("$baseUrl/images/$img", width: 100, height: 100, fit: BoxFit.cover)),
                        ),
                      );
                    }))
              ]);
            }))
      ]),
      floatingActionButton: !isSelection ? FloatingActionButton.extended(onPressed: _pick, icon: const Icon(Icons.add), label: const Text("사진 추가")) : null,
    );
  }
}
