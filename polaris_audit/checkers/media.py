"""
Media accessibility checker.

This module handles media-related accessibility checks including
images, videos, audio, and other media elements.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MediaChecker:
    """Handles media accessibility checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_image_alt_text(self, soup: BeautifulSoup, result: dict) -> None:
        """Check image alt text with improved detection."""
        try:
            imgs = soup.find_all("img")
            missing_alt = 0
            total_imgs = len(imgs)
            problematic_images = []
            
            for img in imgs:
                src = img.get("src", "unknown")
                # Check for missing alt attribute entirely
                if not img.has_attr("alt"):
                    missing_alt += 1
                    problematic_images.append(f"Image '{src}' - needs description for visually impaired users")
                # Check for non-decorative images with empty alt
                elif img.get("alt") == "" and not self._is_decorative_image(img):
                    missing_alt += 1
                    problematic_images.append(f"Image '{src}' - has empty description but appears to contain important content")

            ratio = missing_alt / total_imgs if total_imgs > 0 else 0.0
            
            self.base_checker.set_check_result(result, "img_alt_missing_count", missing_alt)
            self.base_checker.set_check_result(result, "img_alt_missing_ratio", round(ratio, 2))
            self.base_checker.set_check_result(result, "total_images", total_imgs)

            if missing_alt > 0:
                severity = "should_fix" if ratio > 0.2 else "nice_to_have"
                fix_time = min(missing_alt * 3, 45)
                
                self.base_checker.add_business_issue(
                    result,
                    title="Add descriptions to your images",
                    impact=f"{missing_alt} images are invisible to screen reader users",
                    priority=severity,
                    fix_time=fix_time,
                    difficulty="easy",
                    category="accessibility",
                    count=missing_alt,
                    examples=problematic_images,  # Show all examples
                    total_images=total_imgs,
                    element_type="images",
                    technical_details=f"{missing_alt} of {total_imgs} images missing alt text",
                    fix_instructions="Add alt text describing what's shown in each image, or alt='' for decorative images",
                    business_value="Makes your visual content accessible to everyone",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Image Alt Text",
                            "code": "<!-- Descriptive alt text -->\n<img src=\"product.jpg\" alt=\"Red leather handbag with gold hardware\">\n\n<!-- Decorative image -->\n<img src=\"decoration.png\" alt=\"\" role=\"presentation\">",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking images: {str(e)}", "warning", "accessibility")

    def _is_decorative_image(self, img) -> bool:
        """Simple heuristic to identify decorative images."""
        src = img.get("src", "").lower()
        classes = " ".join(img.get("class", [])).lower()
        
        decorative_indicators = [
            "decoration", "decorative", "ornament", "divider", "spacer",
            "background", "border", "icon-decoration", "bullet"
        ]
        
        return any(indicator in src or indicator in classes for indicator in decorative_indicators)

    def check_video_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check video accessibility features."""
        try:
            videos = soup.find_all("video")
            video_issues = 0
            
            for video in videos:
                # Check for controls
                if not video.get("controls"):
                    video_issues += 1
                
                # Check for captions
                if not video.find("track", kind="captions"):
                    video_issues += 1
                
                # Check for descriptive title or aria-label
                if not video.get("title") and not video.get("aria-label"):
                    video_issues += 1
                
                # Check for poster image
                if not video.get("poster"):
                    video_issues += 1
            
            self.base_checker.set_check_result(result, "video_accessibility_issues", video_issues)
            
            if video_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve video accessibility",
                    impact=f"Found {video_issues} video accessibility issues that may prevent some users from accessing content",
                    priority="should_fix",
                    fix_time=60,
                    difficulty="hard",
                    category="accessibility",
                    technical_details=f"Videos need captions, controls, and descriptions for accessibility",
                    fix_instructions="Add captions, controls, and descriptive titles to all videos",
                    business_value="Makes video content accessible to users with hearing or visual impairments",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Video",
                            "code": "<video controls poster=\"thumbnail.jpg\" aria-label=\"Product demonstration\">\n    <source src=\"demo.mp4\" type=\"video/mp4\">\n    <track kind=\"captions\" src=\"captions.vtt\" srclang=\"en\" label=\"English\" default>\n    <track kind=\"descriptions\" src=\"descriptions.vtt\" srclang=\"en\" label=\"English\">\n    <p>Your browser doesn't support video. <a href=\"demo.mp4\">Download video</a></p>\n</video>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking videos: {str(e)}", "warning", "accessibility")

    def check_audio_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check audio accessibility features."""
        try:
            audio_elements = soup.find_all("audio")
            audio_issues = 0
            
            for audio in audio_elements:
                # Check for controls
                if not audio.get("controls"):
                    audio_issues += 1
                
                # Check for descriptive title or aria-label
                if not audio.get("title") and not audio.get("aria-label"):
                    audio_issues += 1
                
                # Check for transcripts
                if not audio.find_next("a", href=re.compile(r'\.(txt|pdf)$', re.I)):
                    audio_issues += 1
            
            self.base_checker.set_check_result(result, "audio_accessibility_issues", audio_issues)
            
            if audio_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve audio accessibility",
                    impact=f"Found {audio_issues} audio accessibility issues that may prevent some users from accessing content",
                    priority="should_fix",
                    fix_time=45,
                    difficulty="medium",
                    category="accessibility",
                    technical_details="Audio content needs controls, descriptions, and transcripts for accessibility",
                    fix_instructions="Add controls, descriptive titles, and transcripts to all audio content",
                    business_value="Makes audio content accessible to users with hearing impairments",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Audio",
                            "code": "<audio controls aria-label=\"Interview with John Doe\">\n    <source src=\"interview.mp3\" type=\"audio/mpeg\">\n    <p>Your browser doesn't support audio. <a href=\"interview.mp3\">Download audio</a></p>\n</audio>\n<p><a href=\"interview-transcript.txt\">Read transcript</a></p>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking audio: {str(e)}", "warning", "accessibility")

    def check_media_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check video and audio accessibility (legacy method for compatibility)."""
        try:
            videos = soup.find_all(["video", "audio"])
            iframes = soup.find_all("iframe", src=re.compile(r'youtube|vimeo|video'))
            
            media_elements = videos + iframes
            issues = 0
            
            for media in media_elements:
                # Check for controls
                if media.name in ["video", "audio"] and not media.get("controls"):
                    issues += 1
                
                # Check for captions (simplified)
                if media.name == "video" and not media.find("track", kind="captions"):
                    issues += 1
                
                # Check for descriptive title
                if not media.get("title") and not media.get("aria-label"):
                    issues += 1
            
            self.base_checker.set_check_result(result, "media_accessibility_issues", issues)
            
            if issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve video/audio accessibility",
                    impact=f"{issues} media elements may not be accessible to all users",
                    priority="nice_to_have",
                    fix_time=45,
                    difficulty="hard",
                    category="accessibility",
                    technical_details="Videos need captions and controls for accessibility",
                    fix_instructions="Add captions to videos and ensure media controls are keyboard accessible",
                    business_value="Makes multimedia content accessible to users with hearing impairments",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Video",
                            "code": "<video controls aria-label=\"Product demonstration\">\n    <source src=\"demo.mp4\" type=\"video/mp4\">\n    <track kind=\"captions\" src=\"captions.vtt\" srclang=\"en\" label=\"English\" default>\n    <p>Your browser doesn't support video. <a href=\"demo.mp4\">Download video</a></p>\n</video>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking media: {str(e)}", "warning", "accessibility")

    def check_image_sizing(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for responsive image sizing and proper dimensions."""
        try:
            imgs = soup.find_all("img")
            sizing_issues = 0
            total_images = len(imgs)
            problematic_images = []

            for img in imgs:
                src = img.get("src", "unknown")
                problems = []

                # Check for missing width/height attributes
                if not img.get("width") and not img.get("height"):
                    problems.append("missing width and height attributes")

                # Check for very large images without responsive sizing
                width = img.get("width")
                if width and width.isdigit() and int(width) > 2000:
                    if not img.get("style") or "max-width" not in img.get("style", ""):
                        problems.append(f"very large image ({width}px wide) without responsive sizing")

                if problems:
                    sizing_issues += 1
                    problems_text = " and ".join(problems)
                    problematic_images.append(f"Image '{src}' - {problems_text} (may not display properly on mobile devices)")

            self.base_checker.set_check_result(result, "image_sizing_issues", sizing_issues)

            if sizing_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve image sizing",
                    impact=f"Found {sizing_issues} images that may not display properly on all devices",
                    priority="nice_to_have",
                    fix_time=30,
                    difficulty="easy",
                    difficulty_description="Add width and height attributes to HTML",
                    category="accessibility",
                    count=sizing_issues,
                    examples=problematic_images,
                    total_elements=total_images,
                    element_type="images",
                    technical_details="Images should have proper dimensions and responsive sizing",
                    fix_instructions="Add width/height attributes and responsive CSS to images",
                    business_value="Improves page loading performance and user experience",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Responsive Images",
                            "code": "<!-- Good: Responsive image with dimensions -->\n<img src=\"hero.jpg\" alt=\"Beautiful landscape\" \n     width=\"800\" height=\"600\" \n     style=\"max-width: 100%; height: auto;\">\n\n<!-- Good: Picture element for different screen sizes -->\n<picture>\n    <source media=\"(max-width: 768px)\" srcset=\"hero-mobile.jpg\">\n    <img src=\"hero-desktop.jpg\" alt=\"Beautiful landscape\" width=\"1200\" height=\"800\">\n</picture>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking image sizing: {str(e)}", "warning", "accessibility")

    def check_figure_captions(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for proper figure and caption usage."""
        try:
            figures = soup.find_all("figure")
            figures_without_captions = 0
            total_figures = len(figures)
            problematic_figures = []

            for i, figure in enumerate(figures):
                if not figure.find("figcaption"):
                    figures_without_captions += 1

                    # Try to identify the figure content
                    img = figure.find("img")
                    if img:
                        img_src = img.get("src", "unknown")
                        img_alt = img.get("alt", "")
                        if img_alt:
                            problematic_figures.append(f"Figure #{i+1} with image '{img_src}' ('{img_alt}') - needs a caption explaining what viewers should learn from it")
                        else:
                            problematic_figures.append(f"Figure #{i+1} with image '{img_src}' - needs both alt text and a caption")
                    else:
                        # Look for other content in figure
                        content_preview = figure.get_text(strip=True)[:50] if figure.get_text(strip=True) else "unknown content"
                        problematic_figures.append(f"Figure #{i+1} containing '{content_preview}' - needs a caption explaining its purpose")

            self.base_checker.set_check_result(result, "figures_without_captions", figures_without_captions)

            if figures_without_captions > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Add captions to figures",
                    impact=f"Found {figures_without_captions} figures without captions that may be unclear to screen reader users",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="easy",
                    category="accessibility",
                    count=figures_without_captions,
                    examples=problematic_figures,
                    total_elements=total_figures,
                    element_type="images",
                    technical_details="Figures should have captions to describe their content",
                    fix_instructions="Wrap images in figure elements and add figcaption for descriptions",
                    business_value="Makes complex images and diagrams accessible to screen reader users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Figure with Caption",
                            "code": "<figure>\n    <img src=\"chart.jpg\" alt=\"Sales data showing 20% increase\">\n    <figcaption>Monthly sales data showing a 20% increase from last quarter</figcaption>\n</figure>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking figure captions: {str(e)}", "warning", "accessibility")

    def check_svg_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check SVG accessibility features."""
        try:
            svgs = soup.find_all("svg")
            svg_issues = 0
            total_svgs = len(svgs)
            problematic_svgs = []

            for i, svg in enumerate(svgs):
                svg_problems = []

                # Check for title or aria-label
                if not svg.find("title") and not svg.get("aria-label"):
                    svg_problems.append("missing title or aria-label")

                # Check for role
                if not svg.get("role") and not svg.get("aria-hidden"):
                    svg_problems.append("missing role or aria-hidden attribute")

                if svg_problems:
                    svg_issues += 1
                    # Get SVG context for identification
                    svg_classes = " ".join(svg.get("class", []))
                    svg_id = svg.get("id", "")

                    identifier = f"SVG #{i+1}"
                    if svg_id:
                        identifier += f" (id='{svg_id}')"
                    elif svg_classes:
                        identifier += f" (class='{svg_classes}')"

                    problems_text = " and ".join(svg_problems)
                    problematic_svgs.append(f"{identifier} - {problems_text} (screen readers can't understand this graphic)")

            self.base_checker.set_check_result(result, "svg_accessibility_issues", svg_issues)

            if svg_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve SVG accessibility",
                    impact=f"Found {svg_issues} SVG elements that may not be accessible to screen reader users",
                    priority="nice_to_have",
                    fix_time=25,
                    difficulty="medium",
                    category="accessibility",
                    count=svg_issues,
                    examples=problematic_svgs,
                    total_elements=total_svgs,
                    element_type="images",
                    technical_details="SVG elements need proper titles and roles for accessibility",
                    fix_instructions="Add title elements and appropriate roles to SVG graphics",
                    business_value="Makes vector graphics accessible to screen reader users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible SVG",
                            "code": "<svg role=\"img\" aria-label=\"Company logo\">\n    <title>Company Logo</title>\n    <circle cx=\"50\" cy=\"50\" r=\"40\" fill=\"blue\"/>\n    <text x=\"50\" y=\"55\" text-anchor=\"middle\" fill=\"white\">ACME</text>\n</svg>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking SVG accessibility: {str(e)}", "warning", "accessibility")
