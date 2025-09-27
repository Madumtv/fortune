<?php
// MegaGPT Fortune & Bio – PHP "full-stack" (no Python)
function search_duckduckgo($query, $max = 12) {
    $q = urlencode($query);
    $url = "https://html.duckduckgo.com/html/?q=$q";
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 14,
        CURLOPT_SSL_VERIFYPEER => false
    ]);
    $html = curl_exec($ch);
    curl_close($ch);

    $links = [];
    if ($html) {
        libxml_use_internal_errors(true);
        $dom = new DOMDocument();
        @$dom->loadHTML($html);
        foreach($dom->getElementsByTagName('a') as $a) {
            $href = $a->getAttribute('href');
            $text = $a->textContent;
            if (strpos($href, 'http') === 0 && !preg_match('#duckduckgo\.com|youtube\.com#', $href)) {
                $links[] = $href;
                if (count($links) >= $max) break;
            }
        }
        libxml_clear_errors();
    }
    return $links;
}

function extract_money($text) {
    // Ajout de variantes (800 M$, 100 millions $, 800 000 000, etc)
    $pattern = '/(\$\s?[\d,.]+(?:\s?million|\s?billion)?|\d+[\s.,]?\d*\s?(million|mille|milliard|millions|USD|euros|euro|dollars)|\d{1,3}(?:[ .]?\d{3})+(?:\$|€| dollars| euros)?)/i';
    preg_match_all($pattern, $text, $matches);
    return $matches[0] ?? [];
}

function clean_money($money_str) {
    $money_str = str_replace([',', '€', '$', 'USD', 'usd', 'euros', 'euro', 'dollars', 'dollar'], ['.', '', '', '', '', '', '', '', ''], strtolower(trim($money_str)));
    if (strpos($money_str, 'million') !== false) {
        return floatval(filter_var($money_str, FILTER_SANITIZE_NUMBER_FLOAT, FILTER_FLAG_ALLOW_FRACTION)) * 1_000_000;
    }
    if (strpos($money_str, 'milliard') !== false || strpos($money_str, 'billion') !== false) {
        return floatval(filter_var($money_str, FILTER_SANITIZE_NUMBER_FLOAT, FILTER_FLAG_ALLOW_FRACTION)) * 1_000_000_000;
    }
    // Gestion 800 000 000, 800.000.000, 800 000 000$
    if (preg_match('/\d{1,3}(?:[ .]?\d{3})+/', $money_str, $n)) {
        return floatval(str_replace([' ', '.'], '', $n[0]));
    }
    if (preg_match('/\d+/', $money_str, $n)) {
        return floatval($n[0]);
    }
    return null;
}

function get_net_worth($name, &$sources) {
    $query = "$name net worth";
    $links = search_duckduckgo($query, 12);
    $net_worths = [];
    $sources = [];

    foreach ($links as $url) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT => 12,
            CURLOPT_SSL_VERIFYPEER => false
        ]);
        $html = curl_exec($ch);
        curl_close($ch);

        if (!$html) continue;
        $text = strip_tags($html);
        $money_matches = extract_money($text);

        $found = false;
        foreach ($money_matches as $m) {
            $money = clean_money($m);
            if ($money && $money > 10_000 && $money < 10_000_000_000) {
                // Vérifie que le nom est dans la phrase autour du montant
                $i = stripos($text, $m);
                if ($i !== false) {
                    $snippet = strtolower(substr($text, max(0, $i-120), strlen($name)+240));
                    if (stripos($snippet, strtolower($name)) !== false) {
                        $net_worths[] = $money;
                        $found = true;
                    }
                }
            }
        }
        if ($found) $sources[] = $url;
    }

    $nb = count($sources);
    if ($nb == 0) {
        return ["Aucune estimation trouvée.", "Aucune estimation fiable trouvée", "danger"];
    }
    $moy = array_sum($net_worths)/count($net_worths)/1_000_000;
    if ($nb >= 3) $fiab = ["Donnée probablement fiable", "success"];
    elseif ($nb == 2) $fiab = ["À prendre avec prudence", "warning"];
    else $fiab = ["Non fiable / source unique", "danger"];
    return [number_format($moy, 1, ',', ' ') . " millions USD (moyenne sur $nb sources)", $fiab[0], $fiab[1]];
}

function get_wikipedia_data($name) {
    $url = "https://fr.wikipedia.org/w/api.php?action=query&format=json&prop=extracts|pageimages&exintro=true&explaintext=true&titles=" . urlencode($name) . "&pithumbsize=180";
    $json = @file_get_contents($url);
    $bio = $img = $wiki_url = null;
    if ($json) {
        $data = json_decode($json, true);
        $page = array_values($data['query']['pages'])[0] ?? [];
        $bio = $page['extract'] ?? "";
        $img = $page['thumbnail']['source'] ?? "";
        $wiki_url = "https://fr.wikipedia.org/wiki/" . str_replace(' ', '_', $name);
        if (!$bio || strlen($bio) < 50) $bio = "Aucun résumé trouvé.";
    }
    return [$bio, $wiki_url, $img];
}

$name = trim($_POST['name'] ?? '');
$result = $fortune = $fiab = $bio = $wiki = $img = '';
$sources = [];

if ($name) {
    list($fortune, $fiab, $fiab_color) = get_net_worth($name, $sources);
    list($bio, $wiki, $img) = get_wikipedia_data($name);
    $result = true;
}
?><!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Estimation Fortune & Bio Personnalités - MegaGPT (PHP only)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        body { background: #fafaff; }
        .photo { width:110px; height:110px; object-fit:cover; border-radius:8px; margin-right:24px; background:#fff; border:1px solid #eee;}
        .source-list { font-size:14px; }
        .wrap-bio { max-height:210px; overflow:auto; background:#fff; border:1px solid #ddd; border-radius:6px; padding:9px 13px;}
    </style>
</head>
<body>
<div class="container py-4">
    <h2 class="mb-3">Estimation Fortune & Bio Personnalités – <span class="text-primary">MegaGPT</span></h2>
    <form method="post" class="mb-4">
        <div class="row g-2 align-items-center">
            <div class="col-auto">
                <input type="text" name="name" class="form-control form-control-lg" style="min-width:230px;" placeholder="Nom de la personnalité" required value="<?=htmlspecialchars($name)?>">
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-success btn-lg">Rechercher</button>
            </div>
        </div>
    </form>
<?php if ($result): ?>
    <div class="mb-2">
        <strong>Résultats pour <?=htmlspecialchars($name)?> :</strong>
    </div>
    <div class="mb-2">
        <span class="fw-semibold">Fortune estimée :</span>
        <span class="badge bg-<?=$fiab_color?>" style="font-size:1em;"><?=$fortune?></span>
    </div>
    <div class="mb-1">
        <span class="fst-italic text-<?=$fiab_color?>">Fiabilité : <?=$fiab?></span>
    </div>
    <div class="row g-2 align-items-start">
        <div class="col-auto">
            <?php if($img): ?><img src="<?=htmlspecialchars($img)?>" class="photo" alt="photo"><?php endif; ?>
        </div>
        <div class="col">
            <div class="wrap-bio"><?=nl2br(htmlspecialchars($bio))?></div>
            <?php if($wiki): ?>
            <div class="mt-2"><a href="<?=htmlspecialchars($wiki)?>" class="btn btn-sm btn-primary" target="_blank">Voir Wikipédia</a></div>
            <?php endif; ?>
        </div>
    </div>
    <div class="mt-3">
        <div class="fw-semibold mb-1">Sources utilisées pour la fortune :</div>
        <ul class="source-list">
        <?php foreach($sources as $src): ?>
            <li><a href="<?=htmlspecialchars($src)?>" target="_blank"><?=htmlspecialchars($src)?></a></li>
        <?php endforeach; ?>
        <?php if(!$sources): ?>
            <li>Aucune source disponible.</li>
        <?php endif; ?>
        </ul>
    </div>
<?php elseif($name): ?>
    <div class="alert alert-danger">Aucun résultat fiable trouvé pour "<?=htmlspecialchars($name)?>".</div>
<?php endif; ?>
    <footer class="mt-4 mb-2 small text-muted text-center">
        MegaGPT Fortune & Bio – Version PHP autonome • <a href="https://github.com/" target="_blank">Voir le projet sur GitHub</a>
    </footer>
</div>
</body>
</html>
